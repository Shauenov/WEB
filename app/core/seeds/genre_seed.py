from sqlmodel import Session
from app.core.db import engine
from app.models import Genre, GenreType


def seed_genres():
    book_genres = [
        "Фантастика",
        "Фэнтези",
        "Детектив",
        "Триллер",
        "Ужасы",
        "Роман",
        "Любовный роман",
        "Исторический роман",
        "Приключения",
        "Научная литература",
        "Учебная литература",
        "Публицистика",
        "Мемуары",
        "Биография",
        "Поэзия",
        "Драматургия",
        "Комедия",
        "Классическая литература",
        "Современная проза",
        "Детская литература",
        "Юмор",
        "Философия",
        "Религия",
        "Саморазвитие",
        "Психология",
        "Бизнес",
        "Экономика",
        "Политика",
        "Социология",
        "Эссе",
        "Критика",
        "Путешествия",
        "Энциклопедии",
        "Справочники",
        "Документальная проза",
        "Научпоп",
        "Мифология",
        "Фольклор"
    ]

    movie_genres = [
        "Боевик",
        "Драма",
        "Комедия",
        "Мелодрама",
        "Фантастика",
        "Фэнтези",
        "Ужасы",
        "Триллер",
        "Детектив",
        "Анимация",
        "Документальный",
        "Приключения",
        "Военный",
        "Исторический",
        "Музыкальный",
        "Спорт",
        "Семейный",
        "Криминал",
        "Короткометражка",
    ]

    music_genres = [
        "Рок",
        "Поп",
        "Джаз",
        "Блюз",
        "Хип-хоп",
        "Рэп",
        "Метал",
        "Классическая музыка",
        "Электронная музыка",
        "Рэгги",
        "Саундтрек",
        "Фолк",
        "Шансон",
        "Инди",
        "Этническая музыка",
        "Панк",
        "Соул",
        "Фанк",
    ]

    with Session(engine) as session:
        for name in book_genres:
            session.add(Genre(name=name, type=GenreType.BOOK, description=None))
        for name in movie_genres:
            session.add(Genre(name=name, type=GenreType.MOVIE, description=None))
        for name in music_genres:
            session.add(Genre(name=name, type=GenreType.MUSIC, description=None))

        session.commit()
        print(f"✅ Добавлено {len(book_genres)} книжных, {len(movie_genres)} кино и {len(music_genres)} музыкальных жанров")
