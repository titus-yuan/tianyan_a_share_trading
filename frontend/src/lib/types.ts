export interface CalendarDay {
  date: string;
  is_open: boolean;
  week_day: number;
}

export interface CalendarMonth {
  year: number;
  month: number;
  days: CalendarDay[];
  stats: { trading_days: number; non_trading_days: number };
}

export interface Tweet {
  id: number;
  tweet_id: number;
  username: string;
  display_name: string;
  content: string;
  posted_at: string;
  raw_url: string;
}

export interface TweetStats {
  total: number;
  today: number;
  accounts: number;
}

export interface PaginatedTweets {
  tweets: Tweet[];
  total: number;
  page: number;
  pages: number;
}
