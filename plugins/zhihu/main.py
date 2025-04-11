import json
import os
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from utils import scheduler

bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    whitelist_groups: List[int]  # 允许使用的群组ID列表
    whitelist_users: List[int]  # 允许使用的用户ID列表
    hot_count: int  # 热榜数量
    answer_count: int  # 回答数量

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 50),
            answer_count=data.get("answer_count", 10),
        )


class ZhihuDataCollector:
    """知乎数据收集器"""

    def __init__(
            self,
            headers_path: Path,
            data_dir: Path,
            answer_count: int = 10,
            debug_mode: bool = False,
    ):
        self.headers = self._load_headers(headers_path)
        self.data_dir = data_dir
        self.answer_count = answer_count
        self.debug_mode = debug_mode  # 调试模式标志，决定是否保存中间数据

    def _load_headers(self, headers_path: Path) -> Dict[str, str]:
        """加载请求头配置"""
        try:
            if headers_path.exists():
                with open(headers_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"警告: 请求头配置文件不存在: {headers_path}")
                return {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": "https://www.zhihu.com/",
                }
        except Exception as e:
            print(f"加载请求头配置出错: {str(e)}")
            return {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www.zhihu.com/",
            }

    def get_zhihu_hot(self) -> List[Dict[str, Any]]:
        """获取知乎热榜数据"""
        url = "https://www.zhihu.com/hot"
        try:
            print(f"开始请求知乎热榜页面: {url}")
            print(f"使用请求头: {self.headers}")

            response = requests.get(url, headers=self.headers)
            print(f"请求状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"获取热榜失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")  # 打印部分响应内容
                return []

            # 调试模式下保存响应内容到文件，用于分析
            if self.debug_mode:
                with open(
                        self.data_dir / "zhihu_hot_response.html", "w", encoding="utf-8"
                ) as f:
                    f.write(response.text)
                print(f"已保存响应内容到 {self.data_dir / 'zhihu_hot_response.html'}")

            print(f"成功获取响应，内容长度: {len(response.text)}")

            soup = BeautifulSoup(response.text, "html.parser")

            # 调试模式下保存解析后的HTML结构，用于调试
            if self.debug_mode:
                with open(
                        self.data_dir / "zhihu_hot_parsed.html", "w", encoding="utf-8"
                ) as f:
                    f.write(str(soup.prettify()))
                print(f"已保存解析后的HTML到 {self.data_dir / 'zhihu_hot_parsed.html'}")

            # 查找所有script标签，输出它们的id，以便找到正确的数据源
            script_tags = soup.find_all("script")
            print(f"页面中发现 {len(script_tags)} 个script标签")
            if self.debug_mode:
                for i, tag in enumerate(script_tags):
                    tag_id = tag.get("id", "无ID")
                    print(f"Script标签 {i + 1}: id={tag_id}, 内容长度={len(str(tag))}")

            script_tag = soup.find("script", id="js-initialData")

            if not script_tag:
                print("未找到包含热榜数据的script标签(js-initialData)")

                # 调试模式下尝试查找其他可能包含数据的script标签
                if self.debug_mode:
                    for tag in script_tags:
                        if len(str(tag)) > 1000 and "hot" in str(tag).lower():
                            print(
                                f"找到可能包含热榜数据的script标签: {tag.get('id', '无ID')}"
                            )
                            with open(
                                    self.data_dir
                                    / f"zhihu_script_{tag.get('id', 'unknown')}.json",
                                    "w",
                                    encoding="utf-8",
                            ) as f:
                                f.write(str(tag.string))

                return []

            print("成功找到js-initialData脚本标签")

            # 调试模式下保存脚本内容，用于分析
            if self.debug_mode:
                with open(
                        self.data_dir / "zhihu_initialData.json", "w", encoding="utf-8"
                ) as f:
                    f.write(str(script_tag.string))
                print(f"已保存初始数据到 {self.data_dir / 'zhihu_initialData.json'}")

            try:
                init_data = json.loads(script_tag.string)
                print("成功解析JSON数据")

                # 调试模式下保存解析后的数据结构
                if self.debug_mode:
                    with open(
                            self.data_dir / "zhihu_parsed_data.json", "w", encoding="utf-8"
                    ) as f:
                        json.dump(init_data, f, ensure_ascii=False, indent=2)
                    print(
                        f"已保存解析后的JSON数据到 {self.data_dir / 'zhihu_parsed_data.json'}"
                    )

                # 检查数据结构
                print(f"初始数据的顶级键: {list(init_data.keys())}")

                if "initialState" not in init_data:
                    print("数据中不包含initialState字段")
                    return []

                print(f"initialState的键: {list(init_data['initialState'].keys())}")

                if "topstory" not in init_data["initialState"]:
                    print("数据中不包含topstory字段")
                    # 尝试查找其他可能的路径
                    print(f"尝试查找包含热榜数据的其他路径...")
                    return []

                print(
                    f"topstory的键: {list(init_data['initialState']['topstory'].keys())}"
                )

                if "hotList" not in init_data["initialState"]["topstory"]:
                    print("数据中不包含hotList字段")
                    return []

                hot_list = init_data["initialState"]["topstory"]["hotList"]
                print(f"成功获取热榜数据，条目数: {len(hot_list)}")

                if len(hot_list) > 0 and self.debug_mode:
                    print(f"第一条热榜数据结构: {list(hot_list[0].keys())}")

                results = []
                for item in hot_list:
                    # 热榜条目的数据结构已更改，需要调整提取逻辑
                    target = item.get("target", {})
                    if not target:
                        continue

                    # 检查是否有 link 字段，知乎热榜新版数据结构中的链接信息
                    link_url = ""
                    if "link" in target and target["link"] and "url" in target["link"]:
                        link_url = target["link"]["url"]

                    # 提取标题
                    title = ""
                    if (
                            "titleArea" in target
                            and target["titleArea"]
                            and "text" in target["titleArea"]
                    ):
                        title = target["titleArea"]["text"]

                    # 提取热度
                    hot_score = ""
                    if (
                            "metricsArea" in target
                            and target["metricsArea"]
                            and "text" in target["metricsArea"]
                    ):
                        hot_score = target["metricsArea"]["text"]

                    # 提取摘要
                    excerpt = ""
                    if (
                            "excerptArea" in target
                            and target["excerptArea"]
                            and "text" in target["excerptArea"]
                    ):
                        excerpt = target["excerptArea"]["text"]

                    # 从URL中提取问题ID
                    question_id = ""
                    if link_url:
                        if "question/" in link_url:
                            # 处理知乎问题链接
                            question_id = link_url.split("question/")[-1].split("/")[0]
                        elif "zhihu.com/question/" in link_url:
                            # 处理完整问题链接
                            question_id = link_url.split("zhihu.com/question/")[
                                -1
                            ].split("/")[0]
                        else:
                            # 尝试直接从URL获取最后一部分作为ID
                            question_id = link_url.split("/")[-1]

                    # 检查是否获取到了必要信息
                    if not title or not link_url:
                        if self.debug_mode:
                            print(f"跳过条目: 缺少标题或链接 - {target}")
                        continue

                    results.append(
                        {
                            "rank": len(results) + 1,
                            "title": title,
                            "question_id": question_id,
                            "url": link_url,
                            "hot_score": hot_score,
                            "excerpt": excerpt,
                        }
                    )

                print(f"成功处理热榜数据，共 {len(results)} 条")
                return results
            except json.JSONDecodeError as je:
                print(f"JSON解析错误: {je}")
                print(f"脚本内容片段: {script_tag.string[:500]}...")
                return []
        except Exception as e:
            print(f"获取知乎热榜出错: {str(e)}")
            return []

    def save_data(self, data: List[Dict[str, Any]]) -> str:
        """保存数据到文件"""
        if not data:
            print("没有数据可保存")
            return ""

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zhihu_hot_{timestamp}.json"
        filepath = self.data_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存至 {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"保存数据失败: {str(e)}")
            return ""


class ZhihuPlugin(BasePlugin):
    name = "ZhihuPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    headers_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None
    debug_mode = False  # 调试模式，决定是否保存中间数据文件

    async def on_load(self):
        """插件加载时的初始化"""
        print(f"ZhihuPlugin 插件加载中...")

        # 初始化配置路径
        self.config_path = Path(__file__).parent / "config" / "config.toml"
        self.headers_path = Path(__file__).parent / "config" / "headers.json"
        self.data_dir = Path(__file__).parent / "data"

        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 初始化定时任务
        scheduler.add_random_minute_task(self.fetch_zhihu_hot, 0, 5)
        scheduler.add_task(self.check_config_update, 30)
        print(f"ZhihuPlugin 插件加载完成")

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    config_data = tomllib.load(f)
                    self.config = Config.from_dict(config_data)
                self.config_last_modified = os.path.getmtime(self.config_path)
                print(f"成功加载 {self.name} 配置")
            else:
                print(f"警告: {self.name} 配置文件不存在: {self.config_path}")
                self.config = Config([], [], 50, 10)  # 默认配置
        except Exception as e:
            print(f"加载 {self.name} 配置出错: {str(e)}")
            self.config = Config([], [], 50, 10)  # 默认配置

    def check_config_update(self) -> bool:
        """检查配置文件是否已更新"""
        try:
            if self.config_path.exists():
                last_modified = os.path.getmtime(self.config_path)
                if last_modified > self.config_last_modified:
                    print(f"{self.name} 配置文件已更新，重新加载")
                    self.load_config()
                    return True
            return False
        except Exception as e:
            print(f"检查 {self.name} 配置更新出错: {str(e)}")
            return False

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """检查用户是否有权限使用此插件"""
        if not self.config:
            return False

        # 检查用户ID是否在白名单中
        if user_id in self.config.whitelist_users:
            return True

        # 如果提供了群组ID，检查群组是否在白名单中
        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    async def fetch_zhihu_hot(self) -> None:
        """获取知乎热榜数据"""
        try:
            print("正在获取知乎热榜数据...")

            # 检查配置是否更新
            if self.check_config_update():
                self.load_config()

            # 创建数据收集器
            collector = ZhihuDataCollector(
                headers_path=self.headers_path,
                data_dir=self.data_dir,
                answer_count=self.config.answer_count if self.config else 10,
                debug_mode=self.debug_mode,
            )

            # 收集数据
            hot_items = collector.get_zhihu_hot()
            if not hot_items:
                print("获取热榜失败")
                return

            # 保存数据
            self.latest_data_file = collector.save_data(hot_items)
            print(f"数据已保存到: {self.latest_data_file}")
        except Exception as e:
            print(f"获取知乎热榜时出错: {str(e)}")
            import traceback

            traceback.print_exc()

    def get_latest_hot_list(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最新的热榜数据"""
        if not self.latest_data_file:
            # 查找最新的数据文件
            data_files = list(self.data_dir.glob("zhihu_hot_*.json"))
            if not data_files:
                return []

            # 按修改时间排序，获取最新的文件
            self.latest_data_file = str(
                sorted(data_files, key=os.path.getmtime, reverse=True)[0]
            )

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 返回前N条热榜
            return data[:count]
        except Exception as e:
            print(f"获取最新热榜数据失败: {str(e)}")
            return []

    def format_hot_list_message(
            self, hot_list: List[Dict[str, Any]], count: int = 10
    ) -> str:
        """格式化热榜消息"""
        if not hot_list:
            return "暂无知乎热榜数据"

        # 限制数量
        hot_list = hot_list[:count]

        # 生成消息
        message = "🔥知乎热榜Top{}🔥\n\n".format(len(hot_list))

        for item in hot_list:
            # 提取标题，去除可能的HTML标签
            title = item.get("title", "").strip()

            # 提取热度
            hot_score = item.get("hot_score", "")

            # 提取链接
            url = item.get("url", "")

            # 添加到消息中
            message += "{}. {}\n热度: {}\n{}\n\n".format(
                item.get("rank", 0), title, hot_score, url
            )

        # 添加时间戳
        message += "更新时间: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return message

    def format_question_detail(self, question_id: str) -> str:
        """格式化问题详情消息，包含高赞回答"""
        # 获取最新数据
        hot_list = self.get_latest_hot_list(
            self.config.hot_count if self.config else 50
        )

        # 查找对应问题
        question_data = None
        for item in hot_list:
            if item.get("question_id") == question_id:
                question_data = item
                break

        if not question_data:
            return f"未找到问题ID为 {question_id} 的数据"

        # 提取信息
        title = question_data.get("title", "").strip()
        url = question_data.get("url", "")
        excerpt = question_data.get("excerpt", "").strip()
        answers = question_data.get("top_answers", [])

        # 生成消息
        message = f"📝问题详情: {title}\n\n"

        if excerpt:
            message += f"📄简介: {excerpt}\n\n"

        message += f"🔗链接: {url}\n\n"

        # 添加高赞回答
        if answers:
            message += f"⭐️高赞回答({len(answers)}条):\n\n"

            for idx, answer in enumerate(answers[:3]):  # 只展示前3条
                author = answer.get("author", "匿名用户")
                content = answer.get("content", "").strip()

                # 限制内容长度
                if len(content) > 100:
                    content = content[:100] + "..."

                message += f"{idx + 1}. 👤{author}: {content}\n\n"

            message += "查看更多回答请访问链接"
        else:
            message += "暂无回答数据"

        return message

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群消息"""
        # 获取群号和发送者QQ
        group_id = msg.group_id
        user_id = msg.user_id

        # 检查权限
        if not self.is_user_authorized(user_id, group_id):
            return

        # 获取消息内容
        content = msg.raw_message.strip()

        # 处理命令
        if content == "知乎热榜":
            # 获取热榜数据
            hot_list = self.get_latest_hot_list(10)  # 默认显示10条
            message = self.format_hot_list_message(hot_list)
            await msg.reply(text=message)
        elif content.startswith("知乎热榜 "):
            # 尝试解析数量参数
            try:
                count = int(content.replace("知乎热榜 ", "").strip())
                count = min(
                    count, self.config.hot_count if self.config else 50
                )  # 限制最大数量
                hot_list = self.get_latest_hot_list(count)
                message = self.format_hot_list_message(hot_list, count)
                await msg.reply(text=message)
            except:
                await msg.reply(text="命令格式错误，正确格式: 知乎热榜 [数量]")
        elif content.startswith("知乎问题 "):
            # 尝试解析问题ID
            try:
                question_id = content.replace("知乎问题 ", "").strip()
                message = self.format_question_detail(question_id)
                await msg.reply(text=message)
            except:
                await msg.reply(text="命令格式错误，正确格式: 知乎问题 [问题ID]")

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        # 获取发送者QQ
        user_id = msg.user_id

        # 检查权限
        if not self.is_user_authorized(user_id):
            return

        # 获取消息内容
        content = msg.raw_message.strip()

        # 处理命令
        if content == "知乎热榜":
            # 获取热榜数据
            hot_list = self.get_latest_hot_list(10)  # 默认显示10条
            message = self.format_hot_list_message(hot_list)
            await msg.reply(text=message)
        elif content.startswith("知乎热榜 "):
            # 尝试解析数量参数
            try:
                count = int(content.replace("知乎热榜 ", "").strip())
                count = min(
                    count, self.config.hot_count if self.config else 50
                )  # 限制最大数量
                hot_list = self.get_latest_hot_list(count)
                message = self.format_hot_list_message(hot_list, count)
                await msg.reply(text=message)
            except:
                await msg.reply(text="命令格式错误，正确格式: 知乎热榜 [数量]")
        elif content.startswith("知乎问题 "):
            # 尝试解析问题ID
            try:
                question_id = content.replace("知乎问题 ", "").strip()
                message = self.format_question_detail(question_id)
                await msg.reply(text=message)
            except:
                await msg.reply(text="命令格式错误，正确格式: 知乎问题 [问题ID]")
