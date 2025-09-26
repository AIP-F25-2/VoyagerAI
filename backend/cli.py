import click
from app import create_app
from app.models import db, Event
from app.services.scraper import scrape_bookmyshow_events
from datetime import datetime


app = create_app()


@click.group()
def cli():
    """VoyagerAI backend command-line interface."""
    pass


@cli.command("init-db")
def init_db_cmd():
    """Create database tables."""
    with app.app_context():
        db.create_all()
        click.echo("✅ Database tables created.")


@cli.command("scrape")
@click.option("--city", default="Mumbai", help="City to scrape events for")
@click.option("--limit", default=10, show_default=True, type=int, help="Max events to scrape")
def scrape_cmd(city: str, limit: int):
    """Scrape events and save into the database."""
    with app.app_context():
        rows = scrape_bookmyshow_events(city=city, limit=limit)
        saved = 0
        for data in rows:
            if not data.get("url"):
                continue
            exists = Event.query.filter_by(url=data["url"]).first()
            if exists:
                continue
            event_date = None
            event_time = None
            if data.get("date"):
                try:
                    event_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
                except Exception:
                    pass
            if data.get("time"):
                try:
                    event_time = datetime.strptime(data["time"], "%H:%M").time()
                except Exception:
                    pass
            ev = Event(
                title=data.get("title", ""),
                date=event_date,
                time=event_time,
                venue=data.get("venue"),
                place=data.get("place"),
                price=data.get("price"),
                url=data.get("url"),
                city=city,
            )
            db.session.add(ev)
            saved += 1
        db.session.commit()
        click.echo(f"✅ Scraped {len(rows)} events, saved {saved} new events.")


@cli.command("runserver")
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=5000, type=int)
def runserver(host: str, port: int):
    """Run the Flask development server."""
    app.run(debug=True, host=host, port=port)


if __name__ == "__main__":
    cli()


