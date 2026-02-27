import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 启用日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量读取机器人 Token（在 Railway 的 Variables 中设置）
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN 环境变量未设置！")
    exit(1)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有转发的消息（兼容新版 python-telegram-bot）"""
    message = update.message
    if not message:
        return

    # 调试：打印是否包含转发来源信息
    logger.info(f"收到消息，是否有转发来源: {hasattr(message, 'forward_origin') and message.forward_origin}")

    original_chat_id = None
    original_message_id = None

    # 新版：通过 forward_origin 获取转发来源
    if hasattr(message, 'forward_origin') and message.forward_origin:
        origin = message.forward_origin
        logger.info(f"forward_origin 类型: {origin.type}, 原始对象: {origin}")
        try:
            if origin.type == 'chat':
                # 来自群组
                original_chat_id = origin.chat.id
                original_message_id = origin.message_id
                logger.info(f"来自 chat: chat_id={original_chat_id}, msg_id={original_message_id}")
            elif origin.type == 'channel':
                # 来自频道
                original_chat_id = origin.chat.id
                original_message_id = origin.message_id
                logger.info(f"来自 channel: chat_id={original_chat_id}, msg_id={original_message_id}")
            elif origin.type == 'user':
                # 来自用户
                original_chat_id = origin.sender_user.id
                original_message_id = origin.message_id
                logger.info(f"来自 user: user_id={original_chat_id}, msg_id={original_message_id}")
            elif origin.type == 'hidden_user':
                # 匿名转发（无法获取原始消息ID，无法复制）
                logger.info("收到匿名转发消息，无法复制")
                return
            else:
                logger.warning(f"未知的 forward_origin 类型: {origin.type}")
                return
        except Exception as e:
            logger.error(f"处理 forward_origin 时出错: {e}")
            return

    # 旧版兼容（如果新版没取到，且存在旧版属性）
    if not original_chat_id:
        if hasattr(message, 'forward_from_chat') and message.forward_from_chat:
            original_chat_id = message.forward_from_chat.id
            original_message_id = message.forward_from_message_id
            logger.info(f"使用旧版 forward_from_chat: chat_id={original_chat_id}, msg_id={original_message_id}")
        elif hasattr(message, 'forward_from') and message.forward_from:
            original_chat_id = message.forward_from.id
            original_message_id = message.forward_from_message_id
            logger.info(f"使用旧版 forward_from: user_id={original_chat_id}, msg_id={original_message_id}")

    if not original_chat_id or not original_message_id:
        logger.warning("无法获取转发来源信息")
        return

    try:
        # 在同一个群组里复制消息
        await message.chat.copy_message(
            from_chat_id=original_chat_id,
            message_id=original_message_id
        )
        logger.info(f"已复制消息 {original_message_id} 到群 {message.chat.id}")
    except Exception as e:
        logger.error(f"复制失败: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    await update.message.reply_text(
        "🤖 克隆机器人已启动！\n\n"
        "把我加到你的群组并设为管理员，然后转发任何消息给我，"
        "我会自动生成一个独立副本。"
    )

def main():
    """主函数：启动机器人"""
    app = Application.builder().token(BOT_TOKEN).build()
    # 添加 /start 命令处理器
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start_command))
    # 添加所有非命令消息的处理器
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    logger.info("机器人启动中...")
    app.run_polling()

if __name__ == "__main__":
    main()
