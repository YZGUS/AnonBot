import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from qqmusic_api import search as qq_search

from scheduler import scheduler
from sender import MessageSender, build_custom_music_card, build_text_message

bot = CompatibleEnrollment


@dataclass
class Config:
    whitelist_groups: List[int]
    whitelist_users: List[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            whitelist_groups=data.get("whitelist", {}).get("group_ids", []),
            whitelist_users=data.get("whitelist", {}).get("user_ids", []),
        )


async def get_top_song(keyword: str) -> Optional[Dict[str, Any]]:
    result = await qq_search.search_by_type(keyword=keyword, num=1)
    top_song = None
    if isinstance(result, list) and len(result) > 0:
        top_song = result[0]
    elif isinstance(result, dict) and "list" in result and result["list"]:
        top_song = result["list"][0]

    if not top_song:
        return None

    return {
        "name": top_song.get("name", "未知歌曲"),
        "singer": [
            singer.get("name", "未知歌手") for singer in top_song.get("singer", [])
        ],
        "singer_str": "、".join(
            [singer.get("name", "未知歌手") for singer in top_song.get("singer", [])]
        )
                      or "未知歌手",
        "mid": top_song.get("mid", ""),
        "songmid": top_song.get("songmid", ""),
        "album": top_song.get("album", {}).get("name", "未知专辑"),
        "raw_data": top_song,  # 保存原始响应数据以便进一步解析
    }


def parse_search_command(command: str) -> Optional[str]:
    command = command.lstrip("/")
    parts = command.split()

    if not parts or parts[0].lower() != "msearch":
        return None

    if len(parts) == 1:
        return None

    keyword = " ".join(parts[1:])
    return keyword


class MusicCardPlugin(BasePlugin):
    name = "MusicCardPlugin"
    version = "0.0.1"

    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    sender = None

    async def on_load(self):
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")

        self.config_path = Path(__file__).parent / "config" / "config.toml"
        self.data_dir = Path(__file__).parent / "data"

        self.sender = MessageSender()

        os.makedirs(self.data_dir, exist_ok=True)
        self.load_config()
        scheduler.add_task(self.check_config_update, 30)

    def load_config(self) -> None:
        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    config_data = tomllib.load(f)
                    self.config = Config.from_dict(config_data)
                self.config_last_modified = os.path.getmtime(self.config_path)
                print(f"成功加载 {self.name} 配置")
            else:
                print(f"警告: {self.name} 配置文件不存在: {self.config_path}")
                self.config = Config([], [])
        except Exception as e:
            print(f"加载 {self.name} 配置出错: {str(e)}")
            self.config = Config([], [])

    def check_config_update(self) -> bool:
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
        if not self.config:
            return False

        if not self.config.whitelist_groups and not self.config.whitelist_users:
            return True

        if user_id in self.config.whitelist_users:
            return True

        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    async def search_and_send_music_card(
            self,
            keyword: str,
            group_id: Optional[int] = None,
            user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        try:
            song = await get_top_song(keyword)
            if not song:
                return {
                    "status": "failed",
                    "message": f"未找到与 '{keyword}' 相关的歌曲",
                }

            song_id = song.get("mid", "") or song.get("songmid", "")
            if not song_id:
                return {"status": "failed", "message": "找到的歌曲没有有效ID"}

            song_name = song.get("name", "未知歌曲")
            singer_str = song.get("singer_str", "未知歌手")
            album = song.get("album", "未知专辑")
            song_info = f"找到歌曲: {song_name} - {singer_str}，专辑: {album}"

            # 从原始数据中提取更多信息
            raw_data = song.get("raw_data", {})

            # 构建自定义URL和音频链接
            url = f"https://y.qq.com/n/ryqq/songDetail/{song_id}"

            # 默认音频链接
            audio_url = "https://demo.com/audio.mp3"

            # 尝试从原始数据中获取图片链接
            image_url = ""
            if "album" in raw_data and isinstance(raw_data["album"], dict):
                album_mid = raw_data["album"].get("mid", "")
                if album_mid:
                    # QQ音乐专辑封面图片格式
                    image_url = f"https://y.qq.com/music/photo_new/T002R300x300M000{album_mid}.jpg"

            if not image_url:
                image_url = "http://p2.music.126.net/6KnDIvgOCXLAVw1M7XTMbg==/678398674349946.jpg?param=130y130"

            # 构建自定义音乐卡片
            music_card = build_custom_music_card(
                url=url,
                audio=audio_url,
                title=song_name,
                image=image_url,
                singer=singer_str,
            )
            if group_id:
                await self.sender.send_group_msg(group_id, {"group_id": group_id, "message": [music_card]})
            elif user_id:
                await self.sender.send_private_msg(user_id, {"user_id": user_id, "message": [music_card]})
            else:
                return {"status": "failed", "message": "未指定发送目标"}

            return {"status": "success", "song_info": song_info}

        except Exception as e:
            print(f"搜索歌曲出错: {str(e)}")
            return {"status": "failed", "message": f"搜索出错: {str(e)}"}

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        message_content = msg.raw_message
        user_id = msg.user_id
        group_id = msg.group_id

        if not self.is_user_authorized(user_id, group_id):
            return

        search_keyword = parse_search_command(message_content)
        if search_keyword:
            result = await self.search_and_send_music_card(
                keyword=search_keyword, group_id=group_id
            )

            if result["status"] == "failed":
                error_msg = result.get("message", "搜索音乐失败")
                text_message = build_text_message(f"搜索失败: {error_msg}")
                error_payload = {"group_id": group_id, "message": [text_message]}
                await self.sender.send_group_msg(group_id, error_payload)

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        message_content = msg.raw_message
        user_id = msg.user_id

        if not self.is_user_authorized(user_id):
            return

        search_keyword = parse_search_command(message_content)
        if search_keyword:
            result = await self.search_and_send_music_card(
                keyword=search_keyword, user_id=user_id
            )

            if result["status"] == "failed":
                error_msg = result.get("message", "搜索音乐失败")
                text_message = build_text_message(f"搜索失败: {error_msg}")
                error_payload = {"user_id": user_id, "message": [text_message]}
                await self.sender.send_private_msg(user_id, error_payload)
