from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from common.enums import ServicePackage
from helper.logger_utils import force_log
from services import ChatService
from services.group_package_service import GroupPackageService

# State codes for package flow
PACKAGE_START_DATE_CODE = 1014
PACKAGE_END_DATE_CODE = 1015
AMOUNT_PAID_CODE = 1016
NOTE_CONFIRMATION_CODE = 1017
NOTE_INPUT_CODE = 1018


class PackageHandler:
    def __init__(self):
        self.chat_service = ChatService()
        self.group_package_service = GroupPackageService()

    async def show_user_confirmation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user
    ) -> int:
        try:
            # Display user information with username
            username = user.username if user.username else "N/A"  # type: ignore
            first_name = user.first_name if user.first_name else "N/A"  # type: ignore
            last_name = user.last_name if user.last_name else "N/A"  # type: ignore

            user_info = f"User Found:\n"
            user_info += f"Username: @{username}\n"
            user_info += f"Name: {first_name} {last_name}\n"

            # Get package info from chat if available
            chat_id = context.user_data.get("chat_id_input")
            if chat_id:
                group_package = await self.group_package_service.get_package_by_chat_id(
                    chat_id
                )
                if group_package:
                    user_info += f"Current Package: {group_package.package.value}"
                else:
                    user_info += f"Current Package: No package assigned"
            else:
                user_info += f"Current Package: N/A (no chat specified)"

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"✅ Confirm (@{username})", callback_data="confirm_user"
                    )
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_user")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(user_info, reply_markup=reply_markup)  # type: ignore
            return 1005  # USER_CONFIRMATION_CODE
        except Exception as e:
            force_log(f"Error in show_user_confirmation: {e}", "PackageHandler")
            await update.message.reply_text("Error displaying user information.")  # type: ignore
            return ConversationHandler.END

    @staticmethod
    async def user_confirmation_handler(
            update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                action = query.data

                if action == "confirm_user":
                    # Show package selection
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                ServicePackage.TRIAL.value, callback_data="TRIAL"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.FREE.value, callback_data="FREE"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.BASIC.value, callback_data="BASIC"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.UNLIMITED.value,
                                callback_data="UNLIMITED",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.BUSINESS.value, callback_data="BUSINESS"
                            )
                        ],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "Please choose a subscription package:",
                        reply_markup=reply_markup,
                    )
                    return 1003  # PACKAGE_COMMAND_CODE

                elif action == "cancel_user":
                    await query.edit_message_text("Operation cancelled.")
                    return ConversationHandler.END

            return 1005  # USER_CONFIRMATION_CODE
        except Exception as e:
            force_log(f"Error in user_confirmation_handler: {e}", "PackageHandler")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def package_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                selected_package = query.data

                # Handle package selection buttons
                if selected_package in ["BASIC", "UNLIMITED", "BUSINESS"]:
                    chat_id = context.user_data.get("chat_id_input")

                    if not chat_id:
                        await query.edit_message_text("Chat ID not found.")
                        return ConversationHandler.END

                    # Store selected package for later processing
                    context.user_data["selected_package"] = selected_package

                    # Ask for start date
                    await query.edit_message_text(
                        f"Selected package: {selected_package}\n\n"
                        "Please enter the start date for this package (dd-mm-yyyy format):\n"
                        "Example: 15-01-2024"
                    )
                    return PACKAGE_START_DATE_CODE

            return 1003  # PACKAGE_COMMAND_CODE
        except Exception as e:
            force_log(f"Error in package_button: {e}", "PackageHandler")
            if query:
                await query.edit_message_text(f"Error updating user package: {str(e)}")
            return ConversationHandler.END

    @staticmethod
    async def process_package_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle start date input for package"""
        try:
            start_date_str = update.message.text.strip()  # type: ignore
            
            try:
                context.user_data["package_start_date"] = start_date_str
                
                # Ask for end date
                await update.message.reply_text(  # type: ignore
                    f"Start date set: {start_date_str}\n\n"
                    "Please enter the end date for this package (dd-mm-yyyy format):\n"
                    "Example: 31-12-2024"
                )
                return PACKAGE_END_DATE_CODE
                
            except ValueError:
                await update.message.reply_text(  # type: ignore
                    "Invalid date format. Please use dd-mm-yyyy format (e.g., 15-01-2024):"
                )
                return PACKAGE_START_DATE_CODE
                
        except Exception as e:
            force_log(f"Error in process_package_start_date: {e}", "PackageHandler")
            await update.message.reply_text("Error processing start date.")  # type: ignore
            return ConversationHandler.END

    async def process_package_end_date(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle end date input and ask for amount paid"""
        try:
            end_date_str = update.message.text.strip()  # type: ignore
            
            # Validate date format
            try:
                end_date = datetime.strptime(end_date_str, "%d-%m-%Y")
                start_date = datetime.strptime(context.user_data["package_start_date"], "%d-%m-%Y")
                
                # Validate end date is after start date
                if end_date <= start_date:
                    await update.message.reply_text(  # type: ignore
                        "End date must be after start date. Please enter a valid end date:"
                    )
                    return PACKAGE_END_DATE_CODE
                
                # Store end date
                context.user_data["package_end_date"] = end_date_str
                
                # Ask for amount paid
                await update.message.reply_text(  # type: ignore
                    f"End date set: {end_date_str}\n\n"
                    "Please enter the amount paid for this package:\n"
                    "Example: 25.50"
                )
                return AMOUNT_PAID_CODE
                
            except ValueError:
                await update.message.reply_text(  # type: ignore
                    "Invalid date format. Please use dd-mm-yyyy format (e.g., 31-12-2024):"
                )
                return PACKAGE_END_DATE_CODE
                
        except Exception as e:
            force_log(f"Error in process_package_end_date: {e}", "PackageHandler")
            await update.message.reply_text("Error processing end date.")  # type: ignore
            return ConversationHandler.END

    async def process_amount_paid(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle amount paid input"""
        try:
            amount_str = update.message.text.strip()  # type: ignore
            
            # Validate amount format
            try:
                amount_paid = float(amount_str)
                if amount_paid < 0:
                    await update.message.reply_text(  # type: ignore
                        "Amount must be a positive number. Please enter a valid amount:"
                    )
                    return AMOUNT_PAID_CODE
                
                # Store amount paid
                context.user_data["amount_paid"] = amount_paid
                
                # Ask if user wants to add a note
                keyboard = [
                    [InlineKeyboardButton("✅ Yes, add note", callback_data="add_note")],
                    [InlineKeyboardButton("❌ No, finish setup", callback_data="skip_note")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(  # type: ignore
                    f"Amount paid set: ${amount_paid:.2f}\n\n"
                    "Would you like to add a note for this package?",
                    reply_markup=reply_markup
                )
                return NOTE_CONFIRMATION_CODE
                
            except ValueError:
                await update.message.reply_text(  # type: ignore
                    "Invalid amount format. Please enter a valid number (e.g., 25.50):"
                )
                return AMOUNT_PAID_CODE
                
        except Exception as e:
            force_log(f"Error in process_amount_paid: {e}", "PackageHandler")
            await update.message.reply_text("Error processing amount paid.")  # type: ignore
            return ConversationHandler.END

    async def handle_note_confirmation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle note confirmation buttons"""
        query = update.callback_query
        try:
            if query:
                await query.answer()
                action = query.data

                if action == "add_note":
                    await query.edit_message_text(
                        "Please enter your note for this package:"
                    )
                    return NOTE_INPUT_CODE

                elif action == "skip_note":
                    # Proceed to finalize without note
                    context.user_data["note"] = None
                    return await self.finalize_package_update_with_payment(update, context)

            return NOTE_CONFIRMATION_CODE
        except Exception as e:
            force_log(f"Error in handle_note_confirmation: {e}", "PackageHandler")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def process_note_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle note input"""
        try:
            note = update.message.text.strip()  # type: ignore
            
            # Store note
            context.user_data["note"] = note
            
            # Proceed to finalize with note
            return await self.finalize_package_update_with_payment(update, context)
            
        except Exception as e:
            force_log(f"Error in process_note_input: {e}", "PackageHandler")
            await update.message.reply_text("Error processing note.")  # type: ignore
            return ConversationHandler.END

    async def finalize_package_update_with_payment(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Finalize the package update with payment info and optional note"""
        try:
            # Get stored data
            chat_id = context.user_data.get("chat_id_input")
            chat_name = context.user_data.get("group_name")
            selected_package = context.user_data.get("selected_package")
            start_date_str = context.user_data.get("package_start_date")
            end_date_str = context.user_data.get("package_end_date")
            amount_paid = context.user_data.get("amount_paid")
            note = context.user_data.get("note")
            
            if not all([chat_id, selected_package, start_date_str, end_date_str, amount_paid is not None]):
                await update.message.reply_text("Missing required information.")  # type: ignore
                return ConversationHandler.END
            
            # Convert dates
            start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_date_str, "%d-%m-%Y")

            # Update group package with dates, amount, and note
            await self.group_package_service.get_or_create_group_package(chat_id)

            updated_package = await self.group_package_service.update_package(
                chat_id, 
                ServicePackage(selected_package),
                package_start_date=start_date,
                package_end_date=end_date,
                amount_paid=amount_paid,
                note=note
            )

            if not updated_package:
                await update.message.reply_text("Failed to update group package.")  # type: ignore
                return ConversationHandler.END

            # Update shift settings based on package change
            if ServicePackage(selected_package) == ServicePackage.BUSINESS:
                # When upgrading to business, automatically enable shift
                await self.chat_service.update_chat_enable_shift(chat_id, True)
            elif ServicePackage(selected_package) in [ServicePackage.TRIAL, ServicePackage.FREE]:
                # When downgrading to trial or free, disable shift
                await self.chat_service.update_chat_enable_shift(chat_id, False)

            # Prepare confirmation message
            message = (
                f"✅ Successfully updated package:\n"
                f"• Package: {selected_package}\n"
                f"• Chat ID: {chat_id}\n"
                f"• Chat Name: {chat_name}\n"
                f"• Start Date: {start_date_str}\n"
                f"• End Date: {end_date_str}\n"
                f"• Amount Paid: ${amount_paid:.2f}"
            )
            
            if note:
                message += f"\n• Note: {note}"

            await update.message.reply_text(message)  # type: ignore
            return ConversationHandler.END
            
        except Exception as e:
            force_log(f"Error in finalize_package_update_with_payment: {e}", "PackageHandler")
            await update.message.reply_text("Error finalizing package update.")  # type: ignore
            return ConversationHandler.END