import os, argparse, random, uuid, datetime, json
from faker import Faker
from sqlalchemy import create_engine, text

fake = Faker()
DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/recs")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

CATEGORIES = ["tech","career","music","sports","wellness","volunteering","arts","social"]

def rand_vec(dim):
    import math
    v = [random.random() for _ in range(dim)]
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/norm for x in v]

def gen_event():
    start = fake.date_time_between(start_date="+1d", end_date="+60d", tzinfo=datetime.timezone.utc)
    end = start + datetime.timedelta(hours=random.choice([1,2,3]))
    title = random.choice(["Workshop","Talk","Meetup","Hack Night","Karaoke","Game Night","Fitness Class","Volunteer Day","Concert","Career Panel"]) + " " + fake.word().title()
    desc = fake.paragraph(nb_sentences=3)
    price = random.choice([0,0,0,500,1000,1500])
    url = f"https://example.com/events/{uuid.uuid4()}"
    tags = random.sample(CATEGORIES, k=random.randint(1,3))
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": desc,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "timezone": "America/New_York",
        "location": fake.street_address(),
        "host": fake.company(),
        "price_cents": price,
        "url": url,
        "tags": tags,
        "raw_s3_uri": None,
        "embed": rand_vec(EMBEDDING_DIM),
        "popularity": random.random()
    }

def gen_user():
    return {
        "id": str(uuid.uuid4()),
        "email": fake.unique.email(),
        "display_name": fake.name(),
        "interests": random.sample(CATEGORIES, k=random.randint(2,4)),
        "embed": rand_vec(EMBEDDING_DIM)
    }

def gen_feedback(user_ids, event_ids, n):
    out = []
    for _ in range(n):
        u = random.choice(user_ids)
        e = random.choice(event_ids)
        clicked = random.random() < 0.4
        saved = clicked and random.random() < 0.3
        rsvp = saved and random.random() < 0.4
        dwell = int(random.random() * 120) if clicked else 0
        out.append((u, e, clicked, saved, rsvp, dwell))
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--events", type=int, default=10000)
    p.add_argument("--users", type=int, default=2000)
    p.add_argument("--interactions", type=int, default=100000)
    args = p.parse_args()

    engine = create_engine(DB_URL, future=True)

    print("Seeding users...")
    users = [gen_user() for _ in range(args.users)]
    with engine.begin() as conn:
        for u in users:
            conn.execute(text(
                """
                INSERT INTO users (id, email, display_name, interests, embed)
                VALUES (:id, :email, :display_name, CAST(:interests AS jsonb), :embed)
                """
            ), {
                "id": u["id"],
                "email": u["email"],
                "display_name": u["display_name"],
                "interests": json.dumps(u["interests"]),
                "embed": u["embed"],
            })


    print("Seeding events...")
    events = [gen_event() for _ in range(args.events)]
    with engine.begin() as conn:
        for e in events:
            conn.execute(text(
                """
                INSERT INTO events
                (id, title, description, start_time, end_time, timezone, location, host, price_cents, url, tags, raw_s3_uri, embed, popularity)
                VALUES
                (:id, :title, :description, :start_time, :end_time, :timezone, :location, :host, :price_cents, :url, :tags, :raw_s3_uri, :embed, :popularity)
                """
            ), e)



    print("Seeding feedback...")
    user_ids = [u["id"] for u in users]
    event_ids = [e["id"] for e in events]
    fb = gen_feedback(user_ids, event_ids, args.interactions)
    with engine.begin() as conn:
        for (u,e,clicked,saved,rsvp,dwell) in fb:
            conn.execute(text(
                """
                INSERT INTO feedback (user_id, event_id, clicked, saved, rsvp, dwell_seconds)
                VALUES (:u, :e, :c, :s, :r, :d)
                """
            ), {"u": u, "e": e, "c": clicked, "s": saved, "r": rsvp, "d": dwell})


    print("Done.")

if __name__ == "__main__":
    main()
