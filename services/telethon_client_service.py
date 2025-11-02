import asyncio
import os

from telethon import TelegramClient, events
from telethon.errors import PersistentTimestampInvalidError

from common.enums import ServicePackage
from helper.logger_utils import force_log
from schedulers import MessageVerificationScheduler
from services import ChatService, IncomeService, UserService, GroupPackageService
from services.income_message_processor import IncomeMessageProcessor
from services.threshold_warning_service import ThresholdWarningService


class TelethonClientService:
    def __init__(self):
        self.client: TelegramClient | None = None
        self.service = IncomeService()
        self.scheduler: MessageVerificationScheduler | None = None
        self.chat_service = ChatService()
        self.user_service = UserService()
        self.group_package_service = GroupPackageService()
        self.mobile_number: str | None = None
        self.message_processor = IncomeMessageProcessor(
            income_service=self.service,
            chat_service=self.chat_service
        )

    async def get_username_by_phone(self, phone_number: str) -> str | None:
        """
        Get Telegram username by phone number.
        
        Args:
            phone_number: The phone number to search for (with or without country code)
            
        Returns:
            Username string if found, None if not found or error occurs
        """
        if not self.client:
            force_log("Client not initialized. Cannot get username by phone.")
            return None
            
        try:
            # Clean phone number - remove spaces, dashes, plus signs
            clean_phone = phone_number.replace(" ", "").replace("-", "").replace("+", "")
            
            # Try to resolve the user by phone number
            try:
                user = await self.client.get_entity(f"+{clean_phone}")
                if hasattr(user, 'username') and user.username:
                    force_log(f"Found username '{user.username}' for phone {phone_number}")
                    return user.username
                else:
                    force_log(f"User found for phone {phone_number} but no username set")
                    return None
            except Exception:
                # Try without the plus sign if the first attempt failed
                try:
                    user = await self.client.get_entity(clean_phone)
                    if hasattr(user, 'username') and user.username:
                        force_log(f"Found username '{user.username}' for phone {phone_number}")
                        return user.username
                    else:
                        force_log(f"User found for phone {phone_number} but no username set")
                        return None
                except Exception as e2:
                    force_log(f"Could not find user for phone {phone_number}: {e2}")
                    return None
                    
        except Exception as e:
            force_log(f"Error getting username by phone {phone_number}: {e}")
            return None

    async def start(self, mobile, api_id, api_hash, is_primary: bool = False):
        session_file = f"{mobile}.session"
        
        # Store mobile number for use in register handler
        self.mobile_number = mobile

        # Handle persistent timestamp errors by removing corrupted session
        try:
            self.client = TelegramClient(mobile, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=mobile)  # type: ignore
            # Initialize threshold warning service and attach to income service
            threshold_service = ThresholdWarningService(telethon_client=self.client)
            self.service.threshold_warning_service = threshold_service
            force_log(f"Account {mobile} started...")
        except PersistentTimestampInvalidError:
            force_log(f"Session corrupted for {mobile}, removing session file...")
            if os.path.exists(session_file):
                os.remove(session_file)

            # Recreate client with clean session
            self.client = TelegramClient(mobile, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=mobile)  # type: ignore
            # Initialize threshold warning service and attach to income service
            threshold_service = ThresholdWarningService(telethon_client=self.client)
            self.service.threshold_warning_service = threshold_service
            force_log(f"Account {mobile} restarted with clean session...")
        except TimeoutError as e:
            force_log(f"Connection timeout for {mobile}: {e}")
            force_log("Will retry connection automatically...")
            # Let Telethon handle automatic reconnection
        except Exception as e:
            force_log(f"Error starting client for {mobile}: {e}")
            raise

        # Add a startup log to confirm client is ready
        force_log("Telethon client event handlers registered successfully")

        # For scheduler purposes, primary client gets None to handle NULL registered_by chats
        scheduler_mobile = None if is_primary else mobile

        # Initialize the message verification scheduler
        self.scheduler = MessageVerificationScheduler(self.client, scheduler_mobile)  # type: ignore
        force_log("Message verification scheduler initialized for one-time startup check")

        @self.client.on(events.NewMessage)  # type: ignore
        async def _new_message_listener(event):
            force_log(f"=== NEW MESSAGE EVENT TRIGGERED ===")
            force_log(f"Chat ID: {event.chat_id}, Message: '{event.message.text}'")

            try:
                sender = await event.get_sender()
                # is_bot = getattr(sender, "bot", False)
                username = getattr(sender, "username", "") or ""

                # Only process messages from the specified bots
                allowed_bots = {
                    "ACLEDABankBot",
                    "PayWayByABA_bot",
                    "PLBITBot",
                    "CanadiaMerchant_bot",
                    "HLBCAM_Bot",
                    "vattanac_bank_merchant_prod_bot",
                    "CPBankBot",
                    "SathapanaBank_bot",
                    "chipmongbankpaymentbot",
                    "prasac_merchant_payment_bot",
                    "AMKPlc_bot",
                    "prince_pay_bot",
                    "s7pos_bot",
                    "payment_bk_bot",
                    "CCUBank_bot",
                }
                if username not in allowed_bots:
                    force_log(f"Message from bot '{username}' not in allowed list, ignoring.")
                    return

                # Skip if no message text
                if not event.message.text:
                    force_log("No message text, skipping")
                    return

                force_log(
                    f"Processing message from chat {event.chat_id}: {event.message.text}"
                )
                
                message_id: int = event.message.id
                message_time = event.message.date

                try:
                    await self.message_processor.store_message(
                        chat_id=event.chat_id,
                        message_id=message_id,
                        message_text=event.message.text,
                        origin_username=username,
                        message_time=message_time,
                    )
                except Exception as income_error:
                    force_log(f"ERROR saving income: {income_error}")
                    import traceback

                    force_log(f"Traceback: {traceback.format_exc()}")

            except Exception as e:
                force_log(f"ERROR in message processing: {e}")
                import traceback

                force_log(f"Traceback: {traceback.format_exc()}")

        # Start command handler for private chats
        @self.client.on(events.NewMessage(pattern="/register_me"))  # type: ignore
        async def start_handler(event):
            try:
                force_log(f"Start command from chat {event.chat_id}")
                
                # Only process private chats (not groups)
                if event.is_private:
                    force_log("Start command received in private chat, ignoring")
                    return
                
                # Get sender information
                sender = await event.get_sender()
                registered_user = None
                
                # Check if sender exists and is not anonymous
                if sender and hasattr(sender, "id") and sender.id is not None:
                    registered_user = await self.user_service.create_user(sender)
                    force_log(f"Start command from user {sender.id} in private chat {event.chat_id}")
                
                # Check if chat is already registered
                existing_chat = await self.chat_service.get_chat_by_chat_id(event.chat_id)
                if existing_chat:
                    # Update the existing chat with the current user_id if different
                    if registered_user and existing_chat.user_id != registered_user.id:
                        force_log(f"Updated existing private chat {event.chat_id} with new user {registered_user.id}")
                        await self.chat_service.update_chat_user_id(event.chat_id, registered_user.id)
                        await event.respond(f"✅ Private chat {event.chat_id} is already registered. Updated with current user.")
                    else:
                        force_log(f"Private chat {event.chat_id} already registered with same user")
                        await event.respond(f"✅ Private chat {event.chat_id} is already registered.")
                    return
                
                # Register new private chat
                force_log(f"Proceeding with new private chat registration for chat {event.chat_id}")
                
                # Get chat title (for groups, use group name or default)
                chat_title = getattr(event.chat, "title", f"{event.chat_id}")
                
                success, message = await self.chat_service.register_chat_id(
                    event.chat_id, chat_title, registered_user, self.mobile_number
                )
                
                if success:
                    # Assign STANDARD package for private chat registrations
                    try:
                        await self.group_package_service.create_group_package(
                            event.chat_id, ServicePackage.STANDARD
                        )
                        force_log(f"Assigned STANDARD package to private chat {event.chat_id}")
                    except Exception as package_error:
                        force_log(f"Error assigning STANDARD package to private chat {event.chat_id}: {package_error}")
                        
                    response_message = f"""✅ Welcome! Your private chat has been registered successfully.

🆔 Chat ID: {event.chat_id}
👤 Registered by: {sender.first_name if sender and hasattr(sender, 'first_name') else 'Unknown'}
📦 Package: STANDARD

You can now receive transaction notifications from bank bots in this private chat.

💡 To manage settings and view reports, you can also register this chat in a group with the bot and use /menu commands there."""
                    await event.respond(response_message)
                    force_log(f"Successfully registered private chat {event.chat_id}")
                else:
                    await event.respond(f"❌ Registration failed: {message}")
                    force_log(f"Failed to register private chat {event.chat_id}: {message}")
                    
            except Exception as e:
                force_log(f"Error in start_handler: {e}")
                await event.respond("❌ An error occurred during registration. Please try again.")

        # Run one-time message verification on startup asynchronously (non-blocking)
        async def run_startup_verification():
            force_log("Running one-time startup message verification to catch any missed messages...")
            try:
                await self.scheduler.verify_messages()
                force_log("Startup message verification completed successfully")
            except Exception as e:
                force_log(f"Error during startup message verification: {e}", "TelethonClientService", "ERROR")

        # Start verification in background without blocking client startup
        asyncio.create_task(run_startup_verification())
        force_log("Startup verification queued to run in background")

        # Start the client (periodic scheduler disabled to prevent rate limits)
        force_log("Starting client event listener (periodic verification disabled)")
        await self.client.run_until_disconnected()  # type: ignore
