import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from utils import scheduler

bot = CompatibleEnrollment  # 兼容回调函数注册器


def get_trending():
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    file_path = Path(__file__).parent / "trending" / f"{current_hour}.json"
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                result = "🔥 GitHub Trending 热门项目 🔥\n\n"
                for idx, item in enumerate(data, 1):
                    project = Project.from_dict(item)
                    # 分隔线
                    if idx > 1:
                        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

                    # 项目名称和序号
                    result += f"{idx}. {project.owner}/{project.repo}\n"
                    # 项目链接
                    result += f"📎 {project.url}\n"
                    # 星星和今日新增
                    result += f"⭐ {project.stars:,} (今日 +{project.today_stars})"
                    # 语言
                    if project.language:
                        result += f" | 🔠 {project.language}"
                    # 分叉数
                    result += f" | 🍴 {project.forks:,}\n"
                    # 项目描述
                    if project.description:
                        result += f"📝 {project.description}\n"

                    result += "\n"
                return result
        return "⚠️ 当前暂无 GitHub Trending 数据\n请稍后再试"
    except Exception as e:
        print(f"获取Trending数据失败: {str(e)}")
        return "❌ 读取 GitHub Trending 数据失败"


class GithubPlugin(BasePlugin):
    name = "GithubPlugin"  # 插件名称
    version = "0.0.1"  # 插件版本

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        scheduler.add_task(self.get_trending_task, 60 * 60)

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        if msg.raw_message == "Github":
            await self.api.post_group_msg(
                msg.group_id, text="Ncatbot GitHub 插件测试成功喵"
            )
        elif msg.raw_message == "Github Trending":
            await self.api.post_group_msg(msg.group_id, text=get_trending())

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        if msg.raw_message == "Github":
            await self.api.post_private_msg(
                msg.user_id, text="Ncatbot GitHub 插件测试成功喵"
            )
        elif msg.raw_message == "Github Trending":
            await self.api.post_private_msg(msg.user_id, text=get_trending())

    def get_trending_task(self):
        try:
            response = requests.get("https://github.com/trending")
            response.raise_for_status()
            data = self.parse_github_projects(response.text)
            filename = datetime.now().strftime("%Y-%m-%d-%H.json")
            filepath = Path(__file__).parent / "trending" / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json_data = [project.to_dict() for project in data]
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"成功保存 {len(data)} 个 Trending 项目")
            return True
        except Exception as e:
            print(f"获取Trending数据失败: {str(e)}")
            return False

    def parse_github_projects(self, html):
        try:
            soup = BeautifulSoup(html, "html.parser")
            trending_items = soup.select("div[data-hpc] article.Box-row")
            projects = []
            for item in trending_items:
                projects.append(Project.from_element(item))
            return projects
        except Exception as e:
            print(f"Error parsing GitHub trending: {e}")
            return []


@dataclass
class Project:
    owner: str
    repo: str
    description: str
    language: str
    stars: int
    forks: int
    today_stars: int
    url: str

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            owner=data.get("owner", ""),
            repo=data.get("repo", ""),
            description=data.get("description", ""),
            language=data.get("language", ""),
            stars=data.get("stars", 0),
            forks=data.get("forks", 0),
            today_stars=data.get("today_stars", 0),
            url=data.get("url", ""),
        )

    @classmethod
    def from_element(cls, element) -> "Project":
        """从HTML元素解析项目数据"""
        try:
            owner_repo = element.select_one("h2 a").text.strip().split("/")
            stars = element.select_one('a[href$="/stargazers"]').text.strip()
            forks = element.select_one('a[href$="/forks"]').text.strip()
            today_stars = (
                element.select_one("span.d-inline-block.float-sm-right").text.strip()
                if element.select_one("span.d-inline-block.float-sm-right")
                else "0"
            )

            return cls(
                owner=owner_repo[0].strip(),
                repo=owner_repo[1].strip(),
                description=(
                    element.select_one("p").text.strip()
                    if element.select_one("p")
                    else ""
                ),
                language=(
                    element.select_one("[itemprop='programmingLanguage']").text.strip()
                    if element.select_one("[itemprop='programmingLanguage']")
                    else ""
                ),
                stars=int(stars.replace(",", "")),
                forks=int(forks.replace(",", "")),
                today_stars=int("".join(filter(str.isdigit, today_stars)) or 0),
                url=f"https://github.com{element.select_one('h2 a')['href']}",
            )
        except Exception as e:
            print(f"Error parsing project element: {e}")
            return cls(
                owner="",
                repo="",
                description="",
                language="",
                stars=0,
                forks=0,
                today_stars=0,
                url="",
            )
