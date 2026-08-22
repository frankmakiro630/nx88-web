-- NX88 VIP + Hoàn trả
alter table public.users add column if not exists total_wager bigint not null default 0;
alter table public.users add column if not exists cashback_pending bigint not null default 0;
alter table public.users add column if not exists cashback_total bigint not null default 0;
alter table public.users add column if not exists vip_need bigint not null default 100000;
alter table public.users add column if not exists vip_level integer not null default 1;
alter table public.users add column if not exists vip_progress integer not null default 0;
