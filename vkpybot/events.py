import enum
import typing

if typing.TYPE_CHECKING:
    from vkpybot.types import Message, User


class EventHandler:
    """
    Defines handlers for events from VK_API
    More like interface
    """

    def __init__(self):
        self.__event_handler = {
            EventType.MESSAGE_NEW: self.on_message_new,
            EventType.MESSAGE_EDIT: self.on_message_edit,
            EventType.MESSAGE_REPLY: self.on_message_reply,
            EventType.MESSAGE_ALLOW: self.on_message_allow,
            EventType.MESSAGE_DENY: self.on_message_deny,
            EventType.MESSAGE_TYPING_STATE: self.on_message_typing_state,
            EventType.MESSAGE_EVENT: self.on_message_event,
            EventType.PHOTO_NEW: self.on_photo_new,
            EventType.PHOTO_COMMENT_NEW: self.on_photo_comment_new,
            EventType.PHOTO_COMMENT_EDIT: self.on_photo_comment_edit,
            EventType.PHOTO_COMMENT_RESTORE: self.on_photo_comment_restore,
            EventType.PHOTO_COMMENT_DELETE: self.on_photo_comment_delete,
            EventType.AUDIO_NEW: self.on_audio_new,
            EventType.VIDEO_NEW: self.on_video_new,
            EventType.VIDEO_COMMENT_NEW: self.on_video_comment_new,
            EventType.VIDEO_COMMENT_EDIT: self.on_video_comment_edit,
            EventType.VIDEO_COMMENT_RESTORE: self.on_video_comment_restore,
            EventType.VIDEO_COMMENT_DELETE: self.on_video_comment_delete,
            EventType.WALL_POST_NEW: self.on_wall_post_new,
            EventType.WALL_REPOST: self.on_wall_repost,
            EventType.WALL_REPLY_NEW: self.on_wall_reply_new,
            EventType.WALL_REPLY_EDIT: self.on_wall_reply_edit,
            EventType.WALL_REPLY_RESTORE: self.on_wall_reply_restore,
            EventType.WALL_REPLY_DELETE: self.on_wall_reply_delete,
            EventType.LIKE_ADD: self.on_like_add,
            EventType.LIKE_REMOVE: self.on_like_remove,
            EventType.BOARD_POST_NEW: self.on_board_post_new,
            EventType.BOARD_POST_EDIT: self.on_board_post_edit,
            EventType.BOARD_POST_RESTORE: self.on_board_post_delete,
            EventType.BOARD_POST_DELETE: self.on_board_post_delete
        }

    async def __call__(self, event: 'EventType', **context: dict):
        if event in self.__event_handler:
            await self.__event_handler[event](**context)

    async def on_message_new(self, message: 'Message', client_info: dict):
        pass

    async def on_message_edit(self, message: 'Message'):
        pass

    async def on_message_reply(self, message: 'Message'):
        pass

    async def on_message_allow(self, user: 'User', key: str):
        pass

    async def on_message_deny(self, user: 'User'):
        pass

    async def on_message_typing_state(self, state: str, sender: 'User'):
        pass

    async def on_message_event(self, user: 'User', **context):
        pass

    async def on_photo_new(self, photo, **context):
        pass

    async def on_photo_comment_new(self, comment, photo_id: int, photo_owner_id: int, **context):
        pass

    async def on_photo_comment_edit(self, comment, photo_id: int, photo_owner_id: int, **context):
        pass

    async def on_photo_comment_restore(self, comment, photo_id: int, photo_owner_id: int, **context):
        pass

    # TODO: check if deprecated in VK
    async def on_photo_comment_delete(self, **context):
        pass

    async def on_audio_new(self, audio, **context):
        pass

    async def on_video_new(self, video, **context):
        pass

    async def on_video_comment_new(self, comment, video_id: int, video_owner_id: int, **context):
        pass

    async def on_video_comment_edit(self, comment, video_id: int, video_owner_id: int, **context):
        pass

    async def on_video_comment_restore(self, comment, video_id: int, video_owner_id: int, **context):
        pass

    async def on_video_comment_delete(self, owner_id: int, comment_id: int, user: 'User', deleter: 'User', **context):
        pass

    async def on_wall_post_new(self, **context):
        pass

    async def on_wall_repost(self, **context):
        pass

    async def on_wall_reply_new(self, **context):
        pass

    async def on_wall_reply_edit(self, **context):
        pass

    async def on_wall_reply_restore(self, **context):
        pass

    async def on_wall_reply_delete(self, **context):
        pass

    async def on_like_add(self, **context):
        pass

    async def on_like_remove(self, **context):
        pass

    async def on_board_post_new(self, **context):
        pass

    async def on_board_post_edit(self, **context):
        pass

    async def on_board_post_restore(self, **context):
        pass

    async def on_board_post_delete(self, **context):
        pass


class EventType(enum.Enum):
    """
    Represents events from VK_BOT_API
    """
    # message events
    MESSAGE_NEW = enum.auto()

    MESSAGE_REPLY = enum.auto()
    MESSAGE_EDIT = enum.auto()

    MESSAGE_ALLOW = enum.auto()

    MESSAGE_DENY = enum.auto()

    MESSAGE_TYPING_STATE = enum.auto()

    MESSAGE_EVENT = enum.auto()

    # photo events
    PHOTO_NEW = enum.auto()

    PHOTO_COMMENT_NEW = enum.auto()
    PHOTO_COMMENT_EDIT = enum.auto()
    PHOTO_COMMENT_RESTORE = enum.auto()

    PHOTO_COMMENT_DELETE = enum.auto()

    # audio events
    AUDIO_NEW = enum.auto()

    # video events
    VIDEO_NEW = enum.auto()

    VIDEO_COMMENT_NEW = enum.auto()
    VIDEO_COMMENT_EDIT = enum.auto()
    VIDEO_COMMENT_RESTORE = enum.auto()

    VIDEO_COMMENT_DELETE = enum.auto()

    # wall events
    WALL_POST_NEW = enum.auto()
    WALL_REPOST = enum.auto()

    WALL_REPLY_NEW = enum.auto()
    WALL_REPLY_EDIT = enum.auto()
    WALL_REPLY_RESTORE = enum.auto()

    WALL_REPLY_DELETE = enum.auto()

    # like events
    LIKE_ADD = enum.auto()

    LIKE_REMOVE = enum.auto()

    # board events
    BOARD_POST_NEW = enum.auto()
    BOARD_POST_EDIT = enum.auto()
    BOARD_POST_RESTORE = enum.auto()

    BOARD_POST_DELETE = enum.auto()
