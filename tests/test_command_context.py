"""验证 MP 原生消息命令向插件传递完整会话权限上下文。"""

from unittest.mock import patch

from app.chain.message import MessageChain
from app.command import Command
from app.runtime.events import Event
from app.schemas.types import EventType, NotificationChannel


def test_command_event_preserves_admin_fact_and_original_chat() -> None:
    """斜杠命令事件应保留管理员事实和原始聊天 ID。"""
    chain = MessageChain()
    with patch.object(chain.eventmanager, "send_event") as send_event:
        chain._handle_message_core(
            channel=NotificationChannel.Telegram,
            source="telegram-test",
            userid="10001",
            username="admin",
            text="/sehua FC2",
            is_channel_admin=True,
            original_message_id=123,
            original_chat_id="-100123",
        )

    event_type, payload = send_event.call_args.args
    assert event_type == EventType.CommandExcute
    assert payload["cmd"] == "/sehua FC2"
    assert payload["is_channel_admin"] is True
    assert payload["original_message_id"] == 123
    assert payload["original_chat_id"] == "-100123"


def test_plugin_callback_preserves_admin_fact_and_original_chat() -> None:
    """插件按钮回调事件应保留管理员事实和原始聊天 ID。"""
    chain = MessageChain()
    with patch.object(chain.eventmanager, "send_event") as send_event:
        chain._handle_message_core(
            channel=NotificationChannel.Telegram,
            source="telegram-test",
            userid="10001",
            username="admin",
            text=None,
            is_channel_admin=True,
            original_message_id=456,
            original_chat_id="-100456",
            callback_data="[PLUGIN]SehuaVideo|detail:abc123",
        )

    event_type, payload = send_event.call_args.args
    assert event_type == EventType.MessageAction
    assert payload["plugin_id"] == "SehuaVideo"
    assert payload["is_channel_admin"] is True
    assert payload["username"] == "admin"
    assert payload["original_message_id"] == 456
    assert payload["original_chat_id"] == "-100456"


def test_command_event_forwards_context_to_command_executor() -> None:
    """命令管理器应把权限和会话上下文继续传给具体命令。"""
    command = Command()
    event = Event(
        EventType.CommandExcute,
        {
            "cmd": "/sehua FC2",
            "user": "10001",
            "channel": NotificationChannel.Telegram,
            "source": "telegram-test",
            "is_channel_admin": True,
            "original_message_id": 789,
            "original_chat_id": "-100789",
        },
    )

    with patch.object(command, "get", return_value={"description": "色花搜索"}), patch.object(
        command, "execute"
    ) as execute:
        command.command_event(event)

    execute.assert_called_once_with(
        cmd="/sehua",
        data_str="FC2",
        channel=NotificationChannel.Telegram,
        source="telegram-test",
        userid="10001",
        is_channel_admin=True,
        original_message_id=789,
        original_chat_id="-100789",
    )
