"""
Joha 统一启动入口
"""

from joha.adapter import MessageClient, GroupMessageEvent, config_manager
from joha.core import message_handler, runtime_context
from joha.core.hot_reload import hot_reloader


RUN_CONNECT_CONFIG = {
    # 这里可以临时覆盖 adapter/connection.yaml；None 表示使用 YAML 配置
    "ws_url": None,
    "access_token": None,
    "bot_uin": None,
    "debug": None,
}

WS_URL = RUN_CONNECT_CONFIG["ws_url"] or config_manager.get("napcat.ws_url", "ws://127.0.0.1:3002")
ACCESS_TOKEN = RUN_CONNECT_CONFIG["access_token"] or config_manager.get("napcat.access_token", "")
BOT_UIN = RUN_CONNECT_CONFIG["bot_uin"] or config_manager.get("napcat.bot_uin", "8888888888")
DEBUG = RUN_CONNECT_CONFIG["debug"] if RUN_CONNECT_CONFIG["debug"] is not None else config_manager.get("settings.debug", True)

runtime_context.bot_uin = int(BOT_UIN)

client = MessageClient(
    ws_url=WS_URL,
    access_token=ACCESS_TOKEN,
)


@client.on_group_message()
async def joha_agent(event: GroupMessageEvent):
    await message_handler.process_group_message(event, client.api)


def main() -> None:
    if config_manager.get("settings.hot_reload", False):
        hot_reloader.start()
    client.start(debug=DEBUG)



if __name__ == "__main__":
    main()
