-- ================================================================
-- NeuroFit Database Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- TABLES
-- ================================================================

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID UNIQUE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  age INTEGER CHECK (age > 0 AND age < 120),
  gender TEXT CHECK (gender IN ('male', 'female', 'other')),
  height_cm NUMERIC(5,2) CHECK (height_cm > 0),
  weight_kg NUMERIC(5,2) CHECK (weight_kg > 0),
  existing_conditions TEXT[] DEFAULT ARRAY[]::TEXT[],
  family_history TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  log_date DATE NOT NULL,
  breakfast TEXT,
  lunch TEXT,
  snacks TEXT,
  dinner TEXT,
  water_liters NUMERIC(3,1) CHECK (water_liters >= 0),
  exercise_minutes INTEGER CHECK (exercise_minutes >= 0),
  sleep_hours NUMERIC(3,1) CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
  symptoms TEXT,
  steps_today INTEGER CHECK (steps_today >= 0),
  calories_today NUMERIC(6,1) CHECK (calories_today >= 0),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, log_date)
);

CREATE TABLE IF NOT EXISTS medical_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  illness_description TEXT NOT NULL,
  illness_date DATE,
  prescription_text TEXT,
  prescription_image_url TEXT,   -- stores Supabase Storage public URL
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NOTE: risk_level includes 'Unknown' for cases where Gemini cannot determine level
CREATE TABLE IF NOT EXISTS risk_predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  risk_level TEXT CHECK (risk_level IN ('Low', 'Moderate', 'High', 'Unknown', 'Error')),
  risk_percentages JSONB NOT NULL,
  trend_prediction JSONB,
  recommendations TEXT[],
  key_reasons TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_vitals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_email TEXT UNIQUE NOT NULL,
  steps INTEGER DEFAULT 0,
  heart_rate INTEGER DEFAULT 0,
  sleep_hours NUMERIC(4,2) DEFAULT 0.0,
  calories INTEGER DEFAULT 0,
  source TEXT DEFAULT 'google_fit',
  recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------
-- google_fit_tokens
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS google_fit_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  token_expiry TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- ROW LEVEL SECURITY
-- ================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_fit_tokens ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------
-- Drop existing policies before recreating (safe re-run)
-- ----------------------------------------------------------------
DROP POLICY IF EXISTS "Allow select users" ON users;
DROP POLICY IF EXISTS "Allow insert users" ON users;
DROP POLICY IF EXISTS "Allow update users" ON users;

DROP POLICY IF EXISTS "Allow select daily_logs" ON daily_logs;
DROP POLICY IF EXISTS "Allow insert daily_logs" ON daily_logs;
DROP POLICY IF EXISTS "Allow update daily_logs" ON daily_logs;
DROP POLICY IF EXISTS "Allow delete daily_logs" ON daily_logs;

DROP POLICY IF EXISTS "Allow select medical_history" ON medical_history;
DROP POLICY IF EXISTS "Allow insert medical_history" ON medical_history;
DROP POLICY IF EXISTS "Allow delete medical_history" ON medical_history;

DROP POLICY IF EXISTS "Allow select risk_predictions" ON risk_predictions;
DROP POLICY IF EXISTS "Allow insert risk_predictions" ON risk_predictions;

DROP POLICY IF EXISTS "Allow select google_fit_tokens" ON google_fit_tokens;
DROP POLICY IF EXISTS "Allow insert google_fit_tokens" ON google_fit_tokens;
DROP POLICY IF EXISTS "Allow update google_fit_tokens" ON google_fit_tokens;

-- ----------------------------------------------------------------
-- users
-- ----------------------------------------------------------------
CREATE POLICY "Allow select users" ON users FOR SELECT USING (true);
CREATE POLICY "Allow insert users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update users" ON users FOR UPDATE USING (true);

-- ----------------------------------------------------------------
-- daily_logs
-- ----------------------------------------------------------------
CREATE POLICY "Allow select daily_logs" ON daily_logs FOR SELECT USING (true);
CREATE POLICY "Allow insert daily_logs" ON daily_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update daily_logs" ON daily_logs FOR UPDATE USING (true);
CREATE POLICY "Allow delete daily_logs" ON daily_logs FOR DELETE USING (true);

-- ----------------------------------------------------------------
-- medical_history
-- ----------------------------------------------------------------
CREATE POLICY "Allow select medical_history" ON medical_history FOR SELECT USING (true);
CREATE POLICY "Allow insert medical_history" ON medical_history FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow delete medical_history" ON medical_history FOR DELETE USING (true);

-- ----------------------------------------------------------------
-- risk_predictions
-- ----------------------------------------------------------------
CREATE POLICY "Allow select risk_predictions" ON risk_predictions FOR SELECT USING (true);
CREATE POLICY "Allow insert risk_predictions" ON risk_predictions FOR INSERT WITH CHECK (true);

-- ----------------------------------------------------------------
-- google_fit_tokens
-- ----------------------------------------------------------------
CREATE POLICY "Allow select google_fit_tokens" ON google_fit_tokens FOR SELECT USING (true);
CREATE POLICY "Allow insert google_fit_tokens" ON google_fit_tokens FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update google_fit_tokens" ON google_fit_tokens FOR UPDATE USING (true);


-- ================================================================
-- STORAGE BUCKET SETUP
-- ================================================================
-- Run these lines separately in the Supabase SQL Editor
-- OR create the bucket manually via Dashboard → Storage → New Bucket
--
-- Bucket name : prescriptions
-- Public      : YES (so images can be displayed via public URL)
--
-- To create via SQL:
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('prescriptions', 'prescriptions', true)
-- ON CONFLICT (id) DO NOTHING;
--
-- Storage RLS policy (allow all uploads):
-- CREATE POLICY "Allow uploads to prescriptions"
--   ON storage.objects FOR INSERT
--   WITH CHECK (bucket_id = 'prescriptions');
--
-- CREATE POLICY "Allow public read from prescriptions"
--   ON storage.objects FOR SELECT
--   USING (bucket_id = 'prescriptions');