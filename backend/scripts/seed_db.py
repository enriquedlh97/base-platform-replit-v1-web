"""
Seed the database with a user, category, and post, using the Supabase Admin API for user creation.
"""

import time

from gotrue import UserResponse
from sqlmodel import Session, select

from app.core.db import engine
from app.core.supabase import supabase_admin_client
from app.models import Category, Post, User

# Seed data
SEED_USER_EMAIL: str = "seeduser@example.com"
SEED_CATEGORY_ID: str = "7cc01a01-8fb0-470e-baf9-100504ac1839"
SEED_CATEGORY_NAME: str = "Seed Category"
SEED_POSTS: list[dict[str, str]] = [
    {
        "id": "7efb6e73-2dda-5dad-87fd-551a346a961c",
        "title": "Vero perpauca vocenimam sunt putatem afficillas, et sunt ad eadem est.",
        "content": "Pluribus perpessio titia quidem decoribus fore, spe liberea discipiet idit optionem.",
        "image_url": "https://images.unsplash.com/photo-1717620378135-91fbecabe3ab?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w2Mjc0MjN8MHwxfHJhbmRvbXx8fHx8fHx8fDE3MTk1MDQ1NjN8&ixlib=rb-4.0.3&q=80&w=1080",
    },
    {
        "id": "a1b2c3d4-1111-2222-3333-444455556666",
        "title": "Second post title example.",
        "content": "This is the content for the second seeded post.",
        "image_url": "https://plus.unsplash.com/premium_photo-1742615135329-126469d894be?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "id": "b2c3d4e5-7777-8888-9999-000011112222",
        "title": "Third post title example.",
        "content": "This is the content for the third seeded post.",
        "image_url": "https://images.unsplash.com/photo-1742654230711-f938802dea76?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
    {
        "id": "c3d4e5f6-aaaa-bbbb-cccc-ddddeeeeffff",
        "title": "Fourth post title example.",
        "content": "This is the content for the fourth seeded post.",
        "image_url": "https://images.unsplash.com/photo-1741846562634-a92c13e44fa3?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    },
]


def get_or_create_user(session: Session, email: str) -> User:
    # Check if user already exists in the app DB
    user: User | None = session.exec(select(User).where(User.email == email)).first()
    if user:
        print(f"User with email '{email}' already exists. Skipping creation.")
        return user

    # Create user in Supabase Auth (triggers creation in public.user)
    response: UserResponse = supabase_admin_client.auth.admin.create_user(
        {"email": email, "email_confirm": True, "password": "123456"}
    )
    user_id: str = response.user.id

    # Wait for the trigger to create the public.user row
    for _ in range(50):
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user:
            print(f"User with email '{email}' created with id {user_id}.")
            return user
        time.sleep(0.1)
    raise RuntimeError("User row was not created by trigger in time.")


def seed_category(session: Session) -> None:
    existing_category: Category | None = session.exec(
        select(Category).where(Category.id == SEED_CATEGORY_ID)
    ).first()
    if existing_category:
        print(f"Category with id '{SEED_CATEGORY_ID}' already exists. Skipping.")
        return
    category: Category = Category(id=SEED_CATEGORY_ID, name=SEED_CATEGORY_NAME)
    session.add(category)
    session.commit()
    print(f"Seeded category with id: {SEED_CATEGORY_ID}")


def seed_posts(session: Session, user_id: str) -> None:
    for post_data in SEED_POSTS:
        existing_post: Post | None = session.exec(
            select(Post).where(Post.id == post_data["id"])
        ).first()
        if existing_post:
            print(f"Post with id '{post_data['id']}' already exists. Skipping.")
            continue
        post: Post = Post(
            id=post_data["id"],
            user_id=user_id,
            category_id=SEED_CATEGORY_ID,
            title=post_data["title"],
            content=post_data["content"],
            image_url=post_data["image_url"],
        )
        session.add(post)
        session.commit()
        print(f"Seeded post with id: {post_data['id']}")


def main() -> None:
    with Session(engine) as session:
        user: User = get_or_create_user(session, SEED_USER_EMAIL)
        seed_category(session)
        seed_posts(session, user.id)


if __name__ == "__main__":
    main()
