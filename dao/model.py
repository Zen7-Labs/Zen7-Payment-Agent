from log import logger

from sqlmodel import SQLModel, Field, Relationship

from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
    ENUM as PG_ENUM,
    VARCHAR,
    TIMESTAMP,
    BIGINT,
    NUMERIC,
    DATE,
    TEXT,
    SMALLINT
)
from sqlalchemy import Column

from enum import Enum
import uuid
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class OrderStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"

class SettlementBatchStatus(str, Enum):
    # 'created', 'pending_payout', 'partially_released', 'released', 'failed', 'canceled'
    created = "created"
    pending_payout = "pending_payout"
    partially_released = "partially_released"
    released = "released"
    failed = "failed"
    canceled = "canceled"

class SettlementDetailStatus(str, Enum):
    # 'pending', 'ready', 'releasing', 'released', 'failed', 'void'
    pending = "pending"
    ready = "ready"
    releasing = "releasing"
    released = "released"
    failed = "failed"
    void = "void"

class PayoutStatus(str, Enum):
    # 'created', 'submitted', 'confirmed', 'failed', 'canceled'
    created = "created"
    submitted = "submitted"
    confirmed = "confirmed"
    failed = "failed"
    canceled = "canceled"

class BatchStatus(str, Enum):
    # 'pending', 'running', 'done', 'failed'
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"

class CheckStatus(str, Enum):
    balanced = "balanced"
    amount_mismatch = "amount_mismatch"
    missing_onchain = "missing_onchain"
    missing_offchain = "missing_offchain"
    address_mismatch = "address_mismatch"
    balance_drift = "balance_drift"
    other = "other"

class ErrorStatus(str, Enum):
    # 'processed', 'pending', 'processing', 'ignored'
    processed = "processed"
    pending = "pending"
    processing = "processing"
    ignored = "ignored"

class SourceEvent(str, Enum):
    # 'transfer_completed', 'funds_escrowed', 'funds_released', 'settlement_completed'
    transfer_completed = "transfer_completed"
    funds_escrowed = "funds_escrowed"
    funds_released = "funds_released"
    settlement_completed = "settlement_completed"

class PayType(str, Enum):
    # 'onchain', 'gateway', 'other'
    onchain = "onchain"
    gateway = "gateway"
    other = "other"

class FinalityStatus(str, Enum):
    # 'pending', 'safe', 'finalized'
    pending = "pending"
    safe = "safe"
    finalized = "finalized"

class FeeType(str, Enum):
    # 'PERCENT', 'FLAT', 'NETWORK'
    percent = "percent"
    flat = "flat"
    network = "network"

class OrderItem(SQLModel, table=True):
    __tablename__ = "orders"
    orders_id: Optional[int] = Field(default=None, primary_key=True)
    order_number: str = Field(sa_column=Column(VARCHAR(length=128)))
    user_id: str = Field(sa_column=Column(VARCHAR(length=128)))
    spend_amount: Decimal = Field(default=Decimal(0), sa_column=Column(NUMERIC(precision=78, scale=0)))
    budget: Decimal = Field(default=Decimal(0), sa_column=Column(NUMERIC(precision=78, scale=0)))
    currency: str = Field(sa_column=Column(VARCHAR(length=50)))
    chain: str = Field(sa_column=Column(VARCHAR(length=50)))
    deadline: int = Field(nullable=False)
    status: Optional[OrderStatus] = Field(sa_column=Column(PG_ENUM(OrderStatus), nullable=False))
    status_message: str = Field(sa_column=Column(TEXT))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))

class SettlementBatch(SQLModel, table=True):
    __tablename__ = "settlement_batch"
    settlement_batch_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True), 
            "server_default": "gen_random_uuid()"
        }
    )
    tenant_id: str = Field(sa_column=Column(TEXT, nullable=False))
    merchant_id: str = Field(default=None, sa_column=Column(TEXT))
    payee_address: str = Field(default=None, sa_column=Column(VARCHAR(length=128)))
    chain_id: str = Field(sa_column=Column(TEXT, nullable=False))
    asset_id: str = Field(sa_column=Column(TEXT, nullable=False))
    check_date: date = Field(default=None, sa_column=Column(DATE()))
    period_start: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    period_end: datetime = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    total_count: int = Field(default=0, sa_column=Column(BIGINT))
    total_amount: Decimal = Field(default=Decimal(0), sa_column=Column(NUMERIC(precision=78, scale=0)))
    fee_total: Decimal = Field(default=Decimal(0), sa_column=Column(NUMERIC(precision=78, scale=0)))
    net_total: Decimal = Field(default=Decimal(0), sa_column=Column(NUMERIC(precision=78, scale=0)))
    settlement_status: Optional[SettlementBatchStatus] = Field(sa_column=Column(PG_ENUM(SettlementBatchStatus), default=SettlementBatchStatus.created, nullable=False))
    finance_confirm_status: str = Field(sa_column=Column(TEXT))
    finance_confirm_id: str = Field(sa_column=Column(TEXT))
    finance_confirm_name: str = Field(sa_column=Column(TEXT))
    finance_confirm_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    settlement_details: list["SettlementDetail"] = Relationship(back_populates="settlement_batch")
    payout_instructions: Optional["PayoutInstruction"] = Relationship(back_populates="settlement_batch")

class SettlementDetail(SQLModel, table=True):
    __tablename__ = "settlement_detail"
    settlement_detail_id: Optional[uuid.UUID] = Field(
        default=None, 
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"
        })
    settlement_batch_id: Optional[uuid.UUID] = Field(foreign_key="settlement_batch.settlement_batch_id")
    intent_id: str = Field(sa_column=Column(TEXT))
    tx_hash: str = Field(sa_column=Column(TEXT))
    chain_id: str = Field(sa_column=Column(TEXT, nullable=False))
    payer_address: str = Field(sa_column=Column(VARCHAR(length=128)))
    payee_address: str = Field(sa_column=Column(VARCHAR(length=128)))
    gross_amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), nullable=False, default=0))
    fee_amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), nullable=False, default=0))
    net_amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), nullable=False, default=0))
    settled_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    source_event: Optional[SourceEvent] = Field(sa_column=Column(PG_ENUM(SourceEvent), nullable=False))
    settlement_status: Optional[SettlementDetailStatus] = Field(sa_column=Column(PG_ENUM(SettlementDetailStatus), default=SettlementDetailStatus.pending, nullable=False))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    settlement_batch: SettlementBatch = Relationship(back_populates="settlement_details")


class PayoutInstruction(SQLModel, table=True):
    __tablename__ = "payout_instruction"

    payout_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"            
        }
    )

    settlement_batch_id: Optional[uuid.UUID] = Field(foreign_key="settlement_batch.settlement_batch_id")
    to_address: str = Field(sa_column=Column(VARCHAR(length=128)))
    chain_id: str = Field(sa_column=Column(TEXT, nullable=False))
    asset_id: str = Field(sa_column=Column(TEXT, nullable=False))
    amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), nullable=False))
    gas_estimate: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0)))
    gas_fee_paid: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0)))
    tx_hash: str = Field(sa_column=Column(TEXT))
    submitted_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    executed_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    finality_status: Optional[FinalityStatus] = Field(sa_column=Column(PG_ENUM(FinalityStatus), default=FinalityStatus.pending))
    status: str = Field(sa_column=Column(PG_ENUM(PayoutStatus), default=PayoutStatus.created))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    settlement_batch: SettlementBatch = Relationship(back_populates="payout_instructions")

class MerchantAccountBalance(SQLModel, table=True):
    __tablename__ = "merchant_account_balance"
    balance_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"
        }
    )

    tenant_id: str = Field(sa_column=Column(TEXT, nullable=False))
    merchant_id: str = Field(sa_column=Column(TEXT, nullable=False))
    chain_id: str = Field(sa_column=Column(TEXT, nullable=False))
    asset_id: str = Field(sa_column=Column(TEXT, nullable=False))
    available: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    pending: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    reserved: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))

class CheckAccountBatch(SQLModel, table=True):
    __tablename__ = "check_account_batch"
    check_account_batch_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"
        }
    )

    payment_platform_id: str = Field(sa_column=Column(TEXT))
    platform_name: str = Field(sa_column=Column(TEXT))
    chain_id: str = Field(sa_column=Column(TEXT))
    asset_id: str = Field(sa_column=Column(TEXT))
    check_date: date = Field(default=None, sa_column=Column(DATE()))
    business_volume: int = Field(default=0, sa_column=Column(BIGINT))
    business_amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    channel_volume: int = Field(default=0, sa_column=Column(BIGINT))
    channel_amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    business_poundage: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    channel_poundage: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    error_total: int = Field(default=0, nullable=False)
    batch_status: Optional[BatchStatus] = Field(sa_column=Column(PG_ENUM(BatchStatus), default=BatchStatus.pending))
    check_status: Optional[CheckStatus] = Field(sa_column=Column(PG_ENUM(CheckStatus), default=CheckStatus.balanced))
    finance_confirm_status: str = Field(sa_column=Column(TEXT))
    finance_confirm_id: str = Field(sa_column=Column(TEXT))
    finance_confirm_name: str = Field(sa_column=Column(TEXT))
    finance_confirm_date: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    tenant_id: str = Field(sa_column=Column(TEXT))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))

class CheckStatusInfo(SQLModel, table=True):
    __tablename__ = "check_account_info"
    check_account_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"
        }
    )
    pay_trade_id: str = Field(sa_column=Column(TEXT))
    pay_channel_id: str = Field(sa_column=Column(TEXT))
    bill_id: str = Field(sa_column=Column(TEXT))
    asset_id: str = Field(sa_column=Column(TEXT))
    tx_hash: str = Field(sa_column=Column(TEXT))
    payer_name: str = Field(sa_column=Column(TEXT))
    payee_name: str = Field(sa_column=Column(TEXT))
    payer_address: str = Field(sa_column=Column(VARCHAR(length=128)))
    payee_address: str = Field(sa_column=Column(VARCHAR(length=128)))
    pay_time: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    pay_type: Optional[PayType] = Field(sa_column=Column(PG_ENUM(PayType), default=PayType.onchain, nullable=False))
    trade_cost: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    pay_cost: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), default=0))
    check_status: Optional[CheckStatus] = Field(sa_column=Column(PG_ENUM(CheckStatus), default=CheckStatus.balanced, nullable=False))
    record_type: int = Field(sa_column=Column(SMALLINT, default=0, nullable=False))
    check_datetime: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    tenant_id: str = Field(sa_column=Column(TEXT))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))

class CheckAccountError(SQLModel, table=True):
    error_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"
        }
    )
    account_date: date = Field(sa_column=Column(DATE(), nullable=False))
    check_account_id: Optional[uuid.UUID] = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    happen_time: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    error_remark: str = Field(sa_column=Column(TEXT))
    error_status: Optional[ErrorStatus] = Field(sa_column=Column(PG_ENUM(ErrorStatus), default=ErrorStatus.pending, nullable=False))
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), default=datetime.now()))
    tenant_id: str = Field(sa_column=Column(TEXT))

class OnchainTransferBill(SQLModel, table=True):
    bill_id: Optional[uuid.UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={
            "pg_type": PG_UUID(as_uuid=True),
            "server_default": "gen_random_uuid()"
        }
    )
    chain_id: str = Field(sa_column=Column(TEXT, nullable=False))
    asset_id: str = Field(sa_column=Column(TEXT, nullable=False))
    tx_hash: str = Field(sa_column=Column(TEXT, nullable=False))
    block_number: int = Field(sa_column=Column(BIGINT, nullable=False))
    confirmations: int = Field(nullable=False, default=0)
    finality_status: Optional[FinalityStatus] = Field(sa_column=Column(PG_ENUM(FinalityStatus)))
    from_address: str = Field(sa_column=Column(VARCHAR(length=128), nullable=False))
    to_address: str = Field(sa_column=Column(VARCHAR(length=128), nullable=False))
    amount: Decimal = Field(sa_column=Column(NUMERIC(precision=78, scale=0), nullable=False))
    token_decimals: int = Field(nullable=False)
    timestamp: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    tenant_id: str = Field(sa_column=Column(TEXT))