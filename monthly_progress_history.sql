create table if not exists public.monthly_progress_history (
    user_id text not null,
    month_key text not null,
    learned_count integer not null default 0,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint monthly_progress_history_pkey primary key (user_id, month_key),
    constraint monthly_progress_history_user_check check (user_id in ('david', 'miguel')),
    constraint monthly_progress_history_month_key_check check (month_key ~ '^\d{4}-\d{2}$'),
    constraint monthly_progress_history_learned_count_check check (learned_count >= 0)
);

grant select, insert, update, delete
on public.monthly_progress_history
to service_role;

create or replace function public.set_monthly_progress_history_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

drop trigger if exists set_monthly_progress_history_updated_at on public.monthly_progress_history;

create trigger set_monthly_progress_history_updated_at
before update on public.monthly_progress_history
for each row
execute function public.set_monthly_progress_history_updated_at();

alter table public.monthly_progress_history enable row level security;

drop policy if exists "Allow authenticated read monthly progress history"
on public.monthly_progress_history;

create policy "Allow authenticated read monthly progress history"
on public.monthly_progress_history
for select
using (auth.role() = 'authenticated');

drop policy if exists "Allow authenticated insert monthly progress history"
on public.monthly_progress_history;

create policy "Allow authenticated insert monthly progress history"
on public.monthly_progress_history
for insert
with check (auth.role() = 'authenticated');

drop policy if exists "Allow authenticated update monthly progress history"
on public.monthly_progress_history;

create policy "Allow authenticated update monthly progress history"
on public.monthly_progress_history
for update
using (auth.role() = 'authenticated')
with check (auth.role() = 'authenticated');

drop policy if exists "Allow authenticated delete monthly progress history"
on public.monthly_progress_history;

create policy "Allow authenticated delete monthly progress history"
on public.monthly_progress_history
for delete
using (auth.role() = 'authenticated');
