import os
import logging
from datetime import datetime, timedelta, timezone


ACCOUNT_AGE_LIMIT = timedelta(days=1)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))


async def handle_member_join(member):
    log_channel = member.guild.get_channel(LOG_CHANNEL_ID)
    account_age = datetime.now(timezone.utc) - member.created_at

    log_message = (
        f"🆕 **New Member Joined**\n"
        f"**Display Name**: {member.display_name}\n"
        f"**Username**: {member.name}#{member.discriminator}\n"
        f"**Account Age**: {account_age.days} days\n"
        f"**User ID**: {member.id}\n"
        f"**Mention**: <@{member.id}>"
    )

    if log_channel:
        await log_channel.send(log_message)
        logging.info(log_message)

    # If account age is below the limit, take action
    if account_age < ACCOUNT_AGE_LIMIT:
        warning_message = (
            f"⚠️ **Suspicious Account Alert** ⚠️\n"
            f"<@{member.id}> ({member.name}#{member.discriminator})\n"
            f"Created **{account_age.days} days** ago.\n"
            f"Action: **Kick**"
        )
        if log_channel:
            await log_channel.send(warning_message)
        logging.warning(warning_message)

        await member.kick(
            reason=f"Account too new (Less than {ACCOUNT_AGE_LIMIT.days} days old)"
        )


async def handle_message_delete(message):
    if message.author.bot:
        return

    log_channel = message.guild.get_channel(LOG_CHANNEL_ID)

    log_message = (
        f"❌ **Message Deleted**\n"
        f"**Display Name**: {message.author.display_name}\n"
        f"**Username**: {message.author.name}#{message.author.discriminator}\n"
        f"**message.author**: {message.author.id}\n"
        f"**message.channel**: {message.channel.mention}\n"
        f"**message.author**: <@{message.author.id}>\n"
        f"**message.content**: {message.content if message.content else '[No Text Content]'}"
    )

    if log_channel:
        await log_channel.send(log_message)
        logging.info(log_message)


def setup(bot):
    bot.add_listener(handle_member_join, "on_member_join")
    bot.add_listener(handle_message_delete, "on_message_delete")
