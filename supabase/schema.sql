-- ============================================================
-- NO BS — Daily AI Short : database schema (Postgres / Supabase)
-- Free tier is plenty. Run this in the Supabase SQL editor.
-- ============================================================

create extension if not exists "pgcrypto";

-- One row per daily edition -----------------------------------
create table if not exists editions (
  id            uuid primary key default gen_random_uuid(),
  edition_date  date not null unique,
  status        text not null default 'pending_approval'
                 check (status in ('pending_approval','approved','rejected','published')),
  subject       text,
  payload       jsonb not null default '{}'::jsonb,  -- full edition (heroes + roundup)
  created_at    timestamptz not null default now(),
  approved_at   timestamptz
);

-- Individual deep-dive stories (denormalized for easy querying)
create table if not exists stories (
  id               uuid primary key default gen_random_uuid(),
  edition_id       uuid references editions(id) on delete cascade,
  edition_date     date not null,
  rank             int,
  hero             boolean default false,
  category         text,
  headline         text not null,
  one_liner        text,
  story            text,
  founding_story   text,
  who_should_use   text,
  who_should_buy   text,
  free_alternatives text,
  verdict          text,
  source_links     jsonb default '[]'::jsonb,
  github_stars     int,
  created_at       timestamptz not null default now()
);
create index if not exists stories_edition_idx on stories(edition_date, rank);
create index if not exists stories_category_idx on stories(category);

-- Shorter roundup items ---------------------------------------
create table if not exists roundup_items (
  id            uuid primary key default gen_random_uuid(),
  edition_id    uuid references editions(id) on delete cascade,
  edition_date  date not null,
  category      text,
  text          text,
  source_links  jsonb default '[]'::jsonb
);

-- Approval audit log ------------------------------------------
create table if not exists approvals (
  id           uuid primary key default gen_random_uuid(),
  edition_id   uuid references editions(id) on delete cascade,
  action       text not null check (action in ('approve','reject')),
  actor        text,
  note         text,
  created_at   timestamptz not null default now()
);

-- Email subscribers (newsletter) ------------------------------
create table if not exists subscribers (
  id          uuid primary key default gen_random_uuid(),
  email       text not null unique,
  active      boolean default true,
  created_at  timestamptz not null default now()
);

-- Mobile push tokens ------------------------------------------
create table if not exists push_tokens (
  id          uuid primary key default gen_random_uuid(),
  token       text not null unique,
  platform    text check (platform in ('ios','android','web')),
  created_at  timestamptz not null default now()
);

-- Keep approved_at in sync when status flips to approved -------
create or replace function set_approved_at() returns trigger as $$
begin
  if new.status = 'approved' and (old.status is distinct from 'approved') then
    new.approved_at := now();
  end if;
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_set_approved_at on editions;
create trigger trg_set_approved_at before update on editions
  for each row execute function set_approved_at();

-- ============================================================
-- Row Level Security
--   * public can READ only approved/published editions & stories
--   * writes happen only via the service role (pipeline / server)
-- ============================================================
alter table editions       enable row level security;
alter table stories        enable row level security;
alter table roundup_items  enable row level security;
alter table subscribers    enable row level security;
alter table push_tokens    enable row level security;
alter table approvals      enable row level security;

-- Public read of published content
create policy "public reads approved editions" on editions
  for select using (status in ('approved','published'));
create policy "public reads approved stories" on stories
  for select using (
    exists (select 1 from editions e
            where e.id = stories.edition_id
              and e.status in ('approved','published')));
create policy "public reads approved roundup" on roundup_items
  for select using (
    exists (select 1 from editions e
            where e.id = roundup_items.edition_id
              and e.status in ('approved','published')));

-- Anyone can subscribe / register a push token (insert only)
create policy "anyone can subscribe" on subscribers
  for insert with check (true);
create policy "anyone can register push token" on push_tokens
  for insert with check (true);

-- NOTE: the service_role key bypasses RLS, so the pipeline and the
-- Next.js server actions (approve/reject) can write freely.
