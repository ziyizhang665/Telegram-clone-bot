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

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN 环境变量未设置！")
    exit(1)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有转发的消息（兼容新版 python-telegram-bot）"""
    message = update.message
    if not message:
        return

    # 判断是否为转发消息（新版本推荐使用 forward_origin）
    is_forward = False
    if hasattr(message, 'forward_origin') and message.forward_origin:
        is_forward = True
    elif hasattr(message, 'forward_date') and message.forward_date:  # 兼容旧版
        is_forward = True

    if not is_forward:
        return

    try:
        # 获取原始消息的 chat_id 和 message_id（兼容新旧版）
        original_chat_id = None
        original_message_id = None

        # 新版方式：通过 forward_origin
        if hasattr(message, 'forward_origin') and message.forward_origin:
            origin = message.forward_origin
            if origin.type == 'chat':
                original_chat_id = origin.chat.id
                original_message_id = origin.message_id
            elif origin.type == 'user':
                original_chat_id = origin.sender_user.id
                original_message_id = origin.message_id
            # 其他类型（如匿名管理员）暂不处理

        # 旧版方式：通过 forward_from_chat / forward_from
        elif hasattr(message, 'forward_from_chat') and message.forward_from_chat:
            original_chat_id = message.forward_from_chat.id
            original_message_id = message.forward_from_message_id
        elif hasattr(message, 'forward_from') and message.forward_from:
            original_chat_id = message.forward_from.id
            original_message_id = message.forward_from_message_id

        if not original_chat_id or not original_message_id:
            logger.warning("无法获取转发来源信息")
            return

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
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start_command))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    logger.info("机器人启动中...")
    app.run_polling()

if __name__ == "__main__":
    main()
