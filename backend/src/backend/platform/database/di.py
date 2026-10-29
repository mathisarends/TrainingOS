from collections.abc import AsyncGenerator, AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.settings import AppSettings


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> AppSettings:
        return AppSettings()

    @provide
    async def engine(self, settings: AppSettings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        if engine.dialect.name == "sqlite":

            @event.listens_for(engine.sync_engine, "connect")
            def foreign_keys(connection: object, _: object) -> None:
                # sqlite3's legacy mode otherwise commits a top-level SAVEPOINT.
                connection.isolation_level = None  # type: ignore[attr-defined]
                connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]

            @event.listens_for(engine.sync_engine, "begin")
            def begin(connection: Connection) -> None:
                connection.exec_driver_sql("BEGIN")

        try:
            yield engine
        finally:
            await engine.dispose()

    @provide
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncGenerator[AsyncSession, BaseException | None]:
        async with session_factory() as session:
            try:
                exception = yield session
                if exception is None:
                    await session.commit()
                else:
                    await session.rollback()
            except BaseException:
                await session.rollback()
                raise
