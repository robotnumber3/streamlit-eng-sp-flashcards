-- Run this once in the Supabase SQL Editor for the flashcards project.
--
-- This script does two things:
-- 1. Creates the app tables if they do not exist yet.
-- 2. Adds explicit service_role grants so the Data API access stays explicit.
--
-- The Streamlit app is server-side and prefers SUPABASE_SERVICE_ROLE_KEY when
-- it is configured, so service_role is the important role for this project.

create table if not exists public.user_preferences (
	user_id text primary key,
	theme text not null default 'dark',
	direction_mode text not null default 'random',
	speech_speed integer not null default 5,
	show_hints boolean not null default true,
	auto_speak_spanish boolean not null default false,
	story_reading_speed integer not null default 3,
	story_pause_amount integer not null default 5,
	ai_sentence_tenses text,
	ai_sentence_level text not null default 'beginner',
	ai_examples_min_words integer not null default 12,
	ai_examples_max_words integer not null default 12,
	ai_auto_play_examples boolean not null default false,
	constraint user_preferences_user_check check (user_id in ('david', 'miguel')),
	constraint user_preferences_direction_mode_check check (direction_mode in ('random', 'en_to_es', 'es_to_en')),
	constraint user_preferences_speech_speed_check check (speech_speed between 1 and 5),
	constraint user_preferences_story_reading_speed_check check (story_reading_speed between 1 and 5),
	constraint user_preferences_story_pause_amount_check check (story_pause_amount between 1 and 5),
	constraint user_preferences_ai_examples_min_words_check check (ai_examples_min_words >= 1),
	constraint user_preferences_ai_examples_max_words_check check (ai_examples_max_words >= 1)
);

create table if not exists public.review_items (
	user_id text not null,
	item_key text not null,
	word text not null,
	answer text not null,
	review_count integer not null default 0,
	constraint review_items_pkey primary key (user_id, item_key),
	constraint review_items_user_check check (user_id in ('david', 'miguel')),
	constraint review_items_review_count_check check (review_count >= 0)
);

create table if not exists public.favorite_items (
	user_id text not null,
	item_key text not null,
	word text not null,
	answer text not null,
	constraint favorite_items_pkey primary key (user_id, item_key),
	constraint favorite_items_user_check check (user_id in ('david', 'miguel'))
);

create table if not exists public.deck_progress (
	user_id text not null,
	deck_filename text not null,
	completed_card_ids jsonb not null default '[]'::jsonb,
	constraint deck_progress_pkey primary key (user_id, deck_filename),
	constraint deck_progress_user_check check (user_id in ('david', 'miguel')),
	constraint deck_progress_completed_card_ids_is_array_check check (jsonb_typeof(completed_card_ids) = 'array')
);

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

alter table public.user_preferences enable row level security;
alter table public.review_items enable row level security;
alter table public.favorite_items enable row level security;
alter table public.deck_progress enable row level security;
alter table public.monthly_progress_history enable row level security;

grant select, insert, update, delete
on public.user_preferences
to service_role;

grant select, insert, update, delete
on public.review_items
to service_role;

grant select, insert, update, delete
on public.favorite_items
to service_role;

grant select, insert, update, delete
on public.deck_progress
to service_role;

grant select, insert, update, delete
on public.monthly_progress_history
to service_role;

-- For any new table you add later, repeat this pattern:
--
-- create table if not exists public.your_new_table (...);
-- grant select, insert, update, delete
-- on public.your_new_table
-- to service_role;