import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 启用日志（方便在 Railway 后台查看运行状态）
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量读取机器人 Token（Railway 里会设置）
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN 环境变量未设置！")
    exit(1)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有转发的消息"""
    # 只处理转发的消息
    if update.message and update.message.forward_date:
        try:
            # 获取原始消息的来源
            if update.message.forward_from_chat:
                # 来自频道或群组的消息
                original_chat_id = update.message.forward_from_chat.id
                original_message_id = update.message.forward_from_message_id
            elif update.message.forward_from:
                # 来自用户的消息
                original_chat_id = update.message.forward_from.id
                original_message_id = update.message.forward_from_message_id
            else:
                return

            # 在同一个群组里复制消息
            await update.message.chat.copy_message(
                from_chat_id=original_chat_id,
                message_id=original_message_id
            )
            logger.info(f"已复制消息 {original_message_id} 到群 {update.message.chat.id}")
        except Exception as e:
            logger.error(f"复制失败: {e}")
            # 可选：向用户反馈错误
            # await update.message.reply_text(f"复制失败: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    await update.message.reply_text(
        "🤖 克隆机器人已启动！\n\n"
        "把我加到你的群组并设为管理员，然后转发任何消息给我，"
        "我会自动生成一个独立副本。"
    )

def main():
    """主函数"""
    # 创建 Application
    app = Application.builder().token(BOT_TOKEN).build()

    # 添加处理器
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start_command))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # 启动机器人（使用 polling 模式）
    logger.info("机器人启动中...")
    app.run_polling()

if __name__ == "__main__":
    main()
