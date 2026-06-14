import argparse
from datetime import datetime

from .scraper import (
    load_history, save_history, get_new_news,
    fetch_news, fetch_trending_tw_stock,
    format_telegram, format_telegram_trending,
    send_telegram,
)


def main():
    parser = argparse.ArgumentParser(description="鉅亨網台股新聞自動抓取")
    parser.add_argument("--telegram", action="store_true", help="抓取後發送 Telegram 通知")
    parser.add_argument("--trending", action="store_true", help="抓取 trending 頁面台股區塊")
    parser.add_argument("--system-chrome", action="store_true", help="使用系統 Chrome 而非內建 Chromium")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="指定日期 (YYYY-MM-DD，預設今天)")
    args = parser.parse_args()

    date_str = args.date
    use_system_chrome = args.system_chrome

    if args.trending:
        print("=== 鉅亨網台股頭條（Trending）===")
        news = fetch_trending_tw_stock(use_system_chrome)

        if news:
            print(f"\n抓到 {len(news)} 筆頭條新聞：")
            for n in news:
                print(f"{n['rank']}. {n['title']}")
                print(f"   {n['url']}")

            if args.telegram:
                msgs = format_telegram_trending(news)
                for m in msgs:
                    print(f"\n[通知]\n{m}")
                send_telegram(msgs)
        else:
            print("[警告] 未抓到任何新聞")
        return

    print(f"=== 鉅亨網台股快訊｜{date_str} ===")

    news = fetch_news(date_str, use_system_chrome)
    new_items = get_new_news(date_str, news)

    if not new_items:
        print("[增量] 無新增新聞（今日已全部通知過）")
    else:
        print(f"[增量] 新增 {len(new_items)} 篇")
        save_history(date_str, news)

    if args.telegram and new_items:
        msgs = format_telegram(new_items, date_str)
        for m in msgs:
            print(f"[通知]\n{m}")
        send_telegram(msgs)
    elif args.telegram:
        print("[通知] 無新增，跳過")


if __name__ == "__main__":
    main()
