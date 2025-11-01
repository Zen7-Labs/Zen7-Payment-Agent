-- Enable the UUID generation extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================
-- ENUM Types (Status/Category)
-- =====================
-- Order Status Enum
DO $$ BEGIN 
    CREATE TYPE order_status_enum AS ENUM ('pending', 'success', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Settlement Batch Status Enum
DO $$ BEGIN 
    CREATE TYPE settlement_batch_status_enum AS ENUM ('created', 'pending_payout', 'partially_released', 'released', 'failed', 'canceled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Settlement Detail Status Enum
DO $$ BEGIN 
    CREATE TYPE settlement_detail_status_enum AS ENUM ('pending', 'ready', 'releasing', 'released', 'failed', 'void');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Payout Status Enum
DO $$ BEGIN 
    CREATE TYPE payout_status_enum AS ENUM ('created', 'submitted', 'confirmed', 'failed', 'canceled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Batch Status Enum
DO $$ BEGIN 
    CREATE TYPE batch_status_enum AS ENUM ('pending', 'running', 'done', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Check Status Enum (Reconciliation Status)
DO $$ BEGIN CREATE TYPE check_status_enum AS ENUM (
    'balanced', -- Balanced
    'amount_mismatch', -- Amount Mismatch
    'missing_onchain', -- Missing On-chain Record
    'missing_offchain', -- Missing Off-chain Record
    'address_mismatch', -- Address Mismatch
    'balance_drift', -- Balance Drift (Custody)
    'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Error Status Enum
DO $$ BEGIN 
    CREATE TYPE error_status_enum AS ENUM ('processed', 'pending', 'processing', 'ignored');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Source Event Enum
DO $$ BEGIN 
    CREATE TYPE source_event_enum AS ENUM ('transfer_completed', 'funds_escrowed', 'funds_released', 'settlement_completed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Pay Type Enum
DO $$ BEGIN 
    CREATE TYPE pay_type_enum AS ENUM ('onchain', 'gateway', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Finality Status Enum
DO $$ BEGIN 
    CREATE TYPE finality_status_enum AS ENUM ('pending', 'safe', 'finalized');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
-- Fee Type Enum
DO $$ BEGIN 
    CREATE TYPE fee_type_enum AS ENUM ('percent', 'flat', 'network');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE orders (
    orders_id SERIAL PRIMARY KEY, -- SQLModel's default for primary_key=True and int
    order_number VARCHAR(128),
    user_id VARCHAR(128),
    spend_amount NUMERIC(78, 0) DEFAULT 0, -- Default value is handled by SQLModel/SQLAlchemy but good to include
    budget NUMERIC(78, 0) DEFAULT 0,
    currency VARCHAR(50) DEFAULT 'USDC',
    chain VARCHAR(50) DEFAULT 'sepolia',
    deadline INTEGER NOT NULL, -- Corresponds to int and nullable=False
    status order_status_enum NOT NULL, -- Uses the defined ENUM type and is NOT NULL
    status_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settlement_batch(
    settlement_batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    tenant_id TEXT NOT NULL, -- Tenant Identifier
    merchant_id TEXT, -- Merchant ID (Nullable); Choose between this and payee_address
    payee_address VARCHAR (128), -- Payee Address (Multi-chain address format, EVM recommended EIP-55)
    chain_id TEXT NOT NULL, -- CAIP-2, e.g., eip155:8453
    asset_id TEXT NOT NULL, -- CAIP-19, e.g., eip155:8453/erc20:0x...
    check_date DATE, -- Reconciliation Date; or use period_* for range
    period_start TIMESTAMPTZ, 
    period_end TIMESTAMPTZ, 
    total_count BIGINT NOT NULL DEFAULT 0, -- Number of Settlements
    total_amount NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Total Amount (in smallest unit)
    fee_total NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Total Fees (in smallest unit)
    net_total NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Net Total (in smallest unit)
    settlement_status settlement_batch_status_enum NOT NULL DEFAULT 'created', 
    finance_confirm_status TEXT, -- Finance Confirmation Status (Custom dictionary/value)
    finance_confirm_id TEXT, 
    finance_confirm_name TEXT, 
    finance_confirm_at TIMESTAMPTZ, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE settlement_batch IS 'Settlement Batch Summary: Aggregated by Tenant/Merchant (or Address) + Date Window + Chain/Asset';
COMMENT ON COLUMN settlement_batch.tenant_id IS 'Tenant Identifier';
COMMENT ON COLUMN settlement_batch.merchant_id IS 'Merchant ID (Nullable, choose one with payee_address)';
COMMENT ON COLUMN settlement_batch.payee_address IS 'Payee Address (Multi-chain address, use EIP-55 for EVM)';
COMMENT ON COLUMN settlement_batch.chain_id IS 'CAIP-2 Chain Identifier';
COMMENT ON COLUMN settlement_batch.asset_id IS 'CAIP-19 Asset Identifier';
COMMENT ON COLUMN settlement_batch.check_date IS 'Reconciliation Date';
COMMENT ON COLUMN settlement_batch.total_amount IS 'Total Amount (Integer in smallest unit)';
COMMENT ON COLUMN settlement_batch.fee_total IS 'Total Fees (Integer in smallest unit)';
COMMENT ON COLUMN settlement_batch.net_total IS 'Net Total (Integer in smallest unit)';
COMMENT ON COLUMN settlement_batch.settlement_status IS 'Batch Settlement Status';

CREATE UNIQUE INDEX IF NOT EXISTS ux_settlement_batch_unique ON settlement_batch(tenant_id, chain_id, asset_id, check_date, COALESCE(merchant_id, payee_address)); 
CREATE INDEX IF NOT EXISTS idx_settlement_batch_check_date ON settlement_batch(check_date);
CREATE INDEX IF NOT EXISTS idx_settlement_batch_chain_asset ON settlement_batch(chain_id, asset_id);


CREATE TABLE IF NOT EXISTS settlement_detail (
    settlement_detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    settlement_batch_id UUID NOT NULL,
    intent_id TEXT, -- Business Intent ID (Off-chain)
    tx_hash TEXT, -- On-chain Transaction Hash (Nullable)
    chain_id TEXT NOT NULL, -- CAIP-2
    asset_id TEXT NOT NULL, -- CAIP-19
    token_decimals INT NOT NULL, -- Token Decimals
    payer_address VARCHAR (128), 
    payee_address VARCHAR (128), 
    gross_amount NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Gross Amount (in smallest unit)
    fee_amount NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Fee Amount (in smallest unit)
    net_amount NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Net Amount (in smallest unit)
    settled_at TIMESTAMPTZ, -- Business Confirmation Time
    source_event source_event_enum NOT NULL, -- Source Event
    settlement_status settlement_detail_status_enum NOT NULL DEFAULT 'pending', 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE settlement_detail IS 'Settlement Item Detail: Corresponds to an Intent or On-chain Transaction';
COMMENT ON COLUMN settlement_detail.intent_id IS 'Business Intent ID (Off-chain primary key)';
COMMENT ON COLUMN settlement_detail.tx_hash IS 'On-chain Transaction Hash';
COMMENT ON COLUMN settlement_detail.gross_amount IS 'Gross Amount (Integer in smallest unit)';
COMMENT ON COLUMN settlement_detail.fee_amount IS 'Fee Amount (Integer in smallest unit)';
COMMENT ON COLUMN settlement_detail.net_amount IS 'Net Amount (Integer in smallest unit)';

CREATE INDEX IF NOT EXISTS idx_settlement_detail_batch ON settlement_detail(settlement_batch_id);
CREATE INDEX IF NOT EXISTS idx_settlement_detail_intent ON settlement_detail(intent_id);
CREATE INDEX IF NOT EXISTS idx_settlement_detail_txhash ON settlement_detail(tx_hash);
CREATE INDEX IF NOT EXISTS idx_settlement_detail_payee ON settlement_detail(payee_address);


CREATE TABLE IF NOT EXISTS payout_instruction (
    payout_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    settlement_batch_id UUID NOT NULL, 
    to_address VARCHAR (128) NOT NULL, -- Recipient Address
    chain_id TEXT NOT NULL, 
    asset_id TEXT NOT NULL, 
    amount NUMERIC (78, 0) NOT NULL, -- Payout Amount (in smallest unit)
    gas_estimate NUMERIC (78, 0), -- Estimated Gas Fee (in smallest unit, denominated in asset)
    gas_fee_paid NUMERIC (78, 0), -- Actual Gas Fee Paid (in smallest unit)
    tx_hash TEXT, -- Payout Transaction Hash
    submitted_at TIMESTAMPTZ, -- Submission Time
    executed_at TIMESTAMPTZ, -- Execution Confirmation Time
    finality_status finality_status_enum, -- Finality Status
    status payout_status_enum NOT NULL DEFAULT 'created', 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE payout_instruction IS 'Custody Payout Instruction and Execution Record';
CREATE INDEX IF NOT EXISTS idx_payout_instruction_batch ON payout_instruction (settlement_batch_id);
CREATE INDEX IF NOT EXISTS idx_payout_instruction_chain_asset ON payout_instruction (chain_id, asset_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_payout_instruction_txhash ON payout_instruction (chain_id, tx_hash) WHERE tx_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS merchant_account_balance (
    balance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    tenant_id TEXT NOT NULL, 
    merchant_id TEXT NOT NULL, 
    chain_id TEXT NOT NULL, 
    asset_id TEXT NOT NULL, 
    available NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Available Balance
    pending NUMERIC (78, 0) NOT NULL DEFAULT 0, -- In-transit/Pending Clearing
    reserved NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Reserved/Frozen
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    UNIQUE(tenant_id, merchant_id, chain_id, asset_id)
);
COMMENT ON TABLE merchant_account_balance IS 'Custody Balance Ledger: Available/In-transit/Reserved';


CREATE TABLE IF NOT EXISTS check_account_batch (
    check_account_batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    payment_platform_id TEXT, -- Payment Platform/Channel (Can coexist with chain)
    platform_name TEXT, 
    chain_id TEXT, -- CAIP-2 (Nullable, for aligning with traditional platforms)
    asset_id TEXT, -- CAIP-19 (Nullable)
    check_date DATE NOT NULL, -- Reconciliation Date
    business_volume BIGINT NOT NULL DEFAULT 0, -- System Transaction Volume
    business_amount NUMERIC (78, 0) NOT NULL DEFAULT 0, -- System Amount (in smallest unit)
    channel_volume BIGINT NOT NULL DEFAULT 0, -- Channel/On-chain Transaction Volume
    channel_amount NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Channel/On-chain Amount (in smallest unit)
    business_poundage NUMERIC (78, 0) NOT NULL DEFAULT 0, -- System Handling Fee
    channel_poundage NUMERIC (78, 0) NOT NULL DEFAULT 0, -- Channel Handling Fee
    error_total INT NOT NULL DEFAULT 0, -- Total Number of Error Records
    batch_status batch_status_enum NOT NULL DEFAULT 'pending', 
    check_status check_status_enum NOT NULL DEFAULT 'balanced', 
    finance_confirm_status TEXT, 
    finance_confirm_id TEXT, 
    finance_confirm_name TEXT, 
    finance_confirm_date TIMESTAMPTZ, 
    tenant_id TEXT, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE check_account_batch IS 'Reconciliation Batch Summary: Aggregated by Platform/Chain + Date';
CREATE INDEX IF NOT EXISTS idx_check_account_batch_unique ON check_account_batch (COALESCE(payment_platform_id, chain_id), COALESCE(asset_id, 'n/a'), check_date);
CREATE INDEX IF NOT EXISTS idx_check_account_batch_date ON check_account_batch (check_date);
CREATE INDEX IF NOT EXISTS idx_check_account_batch_tenant ON check_account_batch (tenant_id);

CREATE TABLE IF NOT EXISTS check_account_info (
    check_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  
    pay_trade_id TEXT, -- Local Transaction/Intent ID (Points to different tables based on platform)
    pay_channel_id TEXT, -- Payment Channel Detail ID
    bill_id TEXT, -- Channel Bill Detail ID (Compatible with on-chain or web2 channels)
    chain_id TEXT, -- CAIP-2 (Nullable)
    asset_id TEXT, -- CAIP-19 (Nullable)
    tx_hash TEXT, -- On-chain Hash (Nullable)
    payer_name TEXT, 
    payee_name TEXT, 
    payer_address VARCHAR (128), 
    payee_address VARCHAR (128), 
    pay_time TIMESTAMPTZ, -- Payment Time
    pay_type pay_type_enum NOT NULL DEFAULT 'onchain', 
    trade_cost NUMERIC (78, 0), -- Local Ledger Amount (in smallest unit)
    pay_cost NUMERIC (78, 0), -- Channel Ledger Amount (in smallest unit)
    check_status check_status_enum NOT NULL DEFAULT 'balanced', 
    record_type SMALLINT NOT NULL DEFAULT 0, -- Record Type: 0 Normal/1 Exception
    check_datetime TIMESTAMPTZ, -- Reconciliation Time
    tenant_id TEXT, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE check_account_info IS 'Reconciliation Detail Record: Records amounts and status from both sides';
CREATE INDEX IF NOT EXISTS idx_check_account_info_pay_trade ON check_account_info (pay_trade_id);
CREATE INDEX IF NOT EXISTS idx_check_account_info_bill ON check_account_info (bill_id);
CREATE INDEX IF NOT EXISTS idx_check_account_info_txhash ON check_account_info (tx_hash);
CREATE INDEX IF NOT EXISTS idx_check_account_info_chain_asset ON check_account_info (chain_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_check_account_info_status ON check_account_info (check_status);

CREATE TABLE IF NOT EXISTS check_account_error (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    account_date DATE NOT NULL, -- Accounting Period/Reconciliation Date
    check_account_id UUID NOT NULL,
    happen_time TIMESTAMPTZ NOT NULL, -- Discovery Time
    error_remark TEXT, -- Error Reason/Remarks
    error_status error_status_enum NOT NULL DEFAULT 'pending', 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), 
    tenant_id TEXT
);
COMMENT ON TABLE check_account_error IS 'Reconciliation Error Record: Only stores exceptions';
CREATE INDEX IF NOT EXISTS idx_check_account_error_date ON check_account_error (account_date);
CREATE INDEX IF NOT EXISTS idx_check_account_error_status ON check_account_error (error_status);
CREATE INDEX IF NOT EXISTS idx_check_account_error_fk ON check_account_error (check_account_id);


CREATE TABLE IF NOT EXISTS onchain_transfer_bill (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    chain_id TEXT NOT NULL, -- CAIP-2 
    asset_id TEXT NOT NULL, -- CAIP-19
    tx_hash TEXT NOT NULL, -- Transaction Hash
    block_number BIGINT NOT NULL, -- Block Number
    confirmations INT NOT NULL DEFAULT 0, -- Number of Confirmations
    finality_status finality_status_enum, -- Finality Status
    from_address VARCHAR (128) NOT NULL, 
    to_address VARCHAR (128) NOT NULL, 
    amount NUMERIC (78, 0) NOT NULL, -- Transfer Amount (in smallest unit)
    token_decimals INT NOT NULL, -- Token Decimals
    "timestamp" TIMESTAMPTZ NOT NULL, -- Block Time (UTC)
    tenant_id TEXT
);
COMMENT ON TABLE onchain_transfer_bill IS 'Raw On-chain Bill: Standardized ERC-20/Native Transfer Records';