class MockCallBackEvent:
    def __init__(self, query, parent):
        self.chat_id = query.message.chat_id
        self.data = query.data.encode("utf-8")
        self.query = query
        self.parent = parent
        self.chat = query.message.chat

    async def edit(self, message, buttons=None):
        keyboard = (
            self.parent._convert_buttons_to_keyboard(buttons) if buttons else None
        )
        await self.query.edit_message_text(message, reply_markup=keyboard)

    async def respond(self, message, buttons=None):
        await self.edit(message, buttons)

    async def get_sender(self):
        return query.from_user  # type: ignore
