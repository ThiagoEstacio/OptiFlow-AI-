"""
GraphQL Schema (PDCA #27)

Main GraphQL schema configuration.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import Optional

from app.graphql.resolvers import Query, Mutation
from app.db.session import AsyncSessionLocal
from app.core.deps import get_current_user
from fastapi import Depends, Request


# Create Strawberry schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)


# Context builder for dependency injection
async def get_context(
    request: Request,
    db: AsyncSessionLocal = Depends(AsyncSessionLocal),
):
    """
    Build GraphQL context with database and user.

    This allows resolvers to access:
    - info.context["db"] - Database session
    - info.context["user"] - Current authenticated user
    - info.context["request"] - FastAPI request object
    """
    try:
        # Extract user from request (if authenticated)
        user = None
        try:
            from fastapi import HTTPException
            user = await get_current_user(request)
        except HTTPException:
            # User not authenticated, allow anonymous queries
            pass

        return {
            "db": db,
            "user": user,
            "request": request
        }
    finally:
        # Ensure db session is closed
        if db:
            await db.close()


# Create GraphQL router
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True  # Enable GraphQL Playground in development
)
