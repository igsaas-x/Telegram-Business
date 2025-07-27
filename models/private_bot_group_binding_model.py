from sqlalchemy import Integer, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel
from models.chat_model import Chat


class PrivateBotGroupBinding(BaseModel):
    __tablename__ = "private_bot_group_binding"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    private_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bound_group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_group.id"), nullable=False
    )

    # Relationship to the bound group
    bound_group: Mapped[Chat] = relationship("Chat", backref="private_bot_bindings")