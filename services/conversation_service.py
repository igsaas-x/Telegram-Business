from typing import Optional, Union

from common.enums import QuestionType
from config import get_db_session
from models import BotQuestion


class ConversationService:
    async def save_question(
        self,
        chat_id: int,
        thread_id: int,
        message_id: int,
        question_type: Union[QuestionType, str],
        context_data: Optional[str] = None,
    ) -> BotQuestion:
        """
        Save question
        """
        with get_db_session() as session:
            question_type_value = (
                question_type.value
                if isinstance(question_type, QuestionType)
                else question_type
            )
            new_question = BotQuestion(
                chat_id=chat_id,
                thread_id=thread_id,
                message_id=message_id,
                question_type=question_type_value,
                context_data=context_data,
            )
            session.add(new_question)
            session.commit()  # Commit the transaction to save to database
            return new_question

    async def mark_as_replied(
        self, chat_id: int, thread_id: int, message_id: int
    ) -> type[BotQuestion] | None:
        """
        Mark question as replied
        """
        with get_db_session() as session:
            question = (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id,
                    BotQuestion.thread_id == thread_id,
                    BotQuestion.message_id == message_id,
                    BotQuestion.is_replied == False,  # type: ignore
                )
                .first()
            )

            if question:
                question.mark_as_replied()
                session.commit()  # Commit the transaction to save changes
                return question  # type: ignore
            return None

    async def get_pending_question(
        self, chat_id: int, thread_id: int, question_type: Optional[QuestionType] = None
    ) -> Optional[BotQuestion]:
        """
        Get pending question
        """
        with get_db_session() as session:
            query = session.query(BotQuestion).filter(
                BotQuestion.chat_id == chat_id, 
                BotQuestion.thread_id == thread_id,
                BotQuestion.is_replied == False  # type: ignore
            )

        if question_type:
            query = query.filter(BotQuestion.question_type == question_type.value)

        return query.order_by(BotQuestion.created_at.desc()).first()

    async def get_question_by_message_id(
        self, chat_id: int, thread_id: int, message_id: int
    ) -> Optional[BotQuestion]:
        """
        Get question by message ID
        """
        with get_db_session() as session:
            return (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id, 
                    BotQuestion.thread_id == thread_id,
                    BotQuestion.message_id == message_id
                )
                .first()
            )

    async def get_pending_question_by_type(
        self, chat_id: int, question_type: QuestionType
    ) -> Optional[BotQuestion]:
        """
        Get any pending question by type (for finding thread_id)
        """
        with get_db_session() as session:
            return (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id,
                    BotQuestion.question_type == question_type.value,
                    BotQuestion.is_replied == False  # type: ignore
                )
                .order_by(BotQuestion.created_at.desc())
                .first()
            )

    async def get_pending_question_by_message_id_and_type(
        self, chat_id: int, message_id: int, question_type: QuestionType
    ) -> Optional[BotQuestion]:
        """
        Get pending question by message ID and type
        """
        with get_db_session() as session:
            return (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id,
                    BotQuestion.message_id == message_id,
                    BotQuestion.question_type == question_type.value,
                    BotQuestion.is_replied == False  # type: ignore
                )
                .first()
            )

    async def get_question_by_chat_and_message_id(
        self, chat_id: int, message_id: int
    ) -> Optional[BotQuestion]:
        """
        Get question by chat ID and message ID only (for telethon bot)
        """
        with get_db_session() as session:
            return (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id,
                    BotQuestion.message_id == message_id
                )
                .first()
            )
