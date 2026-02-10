"""
Movie API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from schemas import (
    MovieResponse, MovieListResponse, MovieCreate, MovieUpdate, MessageResponse,
    ReviewResponse, ReviewListResponse, ReviewCreate
)
from repositories.movie import MovieRepository
from repositories.review import ReviewRepository

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=MovieListResponse)
def get_movies(
    query: Optional[str] = Query(None, description="Search query"),
    genres: Optional[str] = Query(None, description="Filter by genres (comma-separated)"),
    category: Optional[str] = Query(None, description="Category filter"),
    sort: Optional[str] = Query("latest", description="Sort by: latest, popular, rating"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get movies with optional search and filters
    
    - **query**: Search in title and synopsis
    - **genres**: Filter by genres (comma-separated, e.g., "액션,드라마")
    - **category**: Category filter (optional)
    - **sort**: Sort order (latest, popular, rating)
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page
    """
    repo = MovieRepository(db)
    skip = (page - 1) * page_size
    
    # Parse genres from comma-separated string
    genre_list = [g.strip() for g in genres.split(",")] if genres else None
    
    movies = repo.search(
        query=query,
        genres=genre_list,
        category=category,
        sort=sort,
        skip=skip,
        limit=page_size
    )
    total = repo.count_search(query=query, genres=genre_list, category=category)
    
    # Convert to response format
    movie_responses = []
    for movie in movies:
        movie_dict = {
            "id": movie.id,
            "title": movie.title,
            "release": movie.release,
            "runtime": movie.runtime,
            "synopsis": movie.synopsis,
            "poster_url": movie.poster_url,
            "created_at": movie.created_at,
            "genres": [g.genre for g in movie.genres],
            "tags": [t.tag for t in movie.tags]
        }
        movie_responses.append(MovieResponse(**movie_dict))
    
    return MovieListResponse(
        movies=movie_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get movie by ID with genres and tags"""
    repo = MovieRepository(db)
    movie = repo.get_with_details(movie_id)
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return MovieResponse(
        id=movie.id,
        title=movie.title,
        release=movie.release,
        runtime=movie.runtime,
        synopsis=movie.synopsis,
        poster_url=movie.poster_url,
        created_at=movie.created_at,
        genres=[g.genre for g in movie.genres],
        tags=[t.tag for t in movie.tags]
    )


@router.get("/{movie_id}/reviews", response_model=ReviewListResponse)
def get_movie_reviews(
    movie_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get reviews for a specific movie"""
    # Check if movie exists
    movie_repo = MovieRepository(db)
    if not movie_repo.get(movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")
    
    review_repo = ReviewRepository(db)
    skip = (page - 1) * page_size
    
    reviews = review_repo.get_by_movie(movie_id, skip=skip, limit=page_size)
    total = review_repo.count(filters={"movie_id": movie_id})
    
    review_responses = []
    for review in reviews:
        result = review_repo.get_with_counts(review.id)
        review_responses.append(
            ReviewResponse(
                id=review.id,
                user_id=review.user_id,
                movie_id=review.movie_id,
                rating=review.rating,
                content=review.content,
                created_at=review.created_at,
                likes_count=result["likes_count"],
                comments_count=result["comments_count"]
            )
        )
    
    return ReviewListResponse(reviews=review_responses, total=total)


@router.post("/{movie_id}/reviews", response_model=ReviewResponse, status_code=201)
def create_movie_review(
    movie_id: int,
    review: ReviewCreate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a review for a specific movie"""
    # Check if movie exists
    movie_repo = MovieRepository(db)
    if not movie_repo.get(movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")
    
    review_repo = ReviewRepository(db)
    
    # Check if user already reviewed this movie
    existing = review_repo.get_user_review_for_movie(user_id, movie_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already reviewed this movie. Use PUT to update."
        )
    
    review_data = review.model_dump()
    review_data["user_id"] = user_id
    review_data["movie_id"] = movie_id
    
    db_review = review_repo.create(review_data)
    
    return ReviewResponse(
        id=db_review.id,
        user_id=db_review.user_id,
        movie_id=db_review.movie_id,
        rating=db_review.rating,
        content=db_review.content,
        created_at=db_review.created_at,
        likes_count=0,
        comments_count=0
    )


@router.post("", response_model=MovieResponse, status_code=201)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    """Create a new movie"""
    repo = MovieRepository(db)
    
    movie_data = movie.model_dump()
    db_movie = repo.create(movie_data)
    
    return MovieResponse(
        id=db_movie.id,
        title=db_movie.title,
        release=db_movie.release,
        runtime=db_movie.runtime,
        synopsis=db_movie.synopsis,
        poster_url=db_movie.poster_url,
        created_at=db_movie.created_at,
        genres=[],
        tags=[]
    )


@router.put("/{movie_id}", response_model=MovieResponse)
def update_movie(movie_id: int, movie: MovieUpdate, db: Session = Depends(get_db)):
    """Update a movie"""
    repo = MovieRepository(db)
    
    movie_data = movie.model_dump(exclude_unset=True)
    db_movie = repo.update(movie_id, movie_data)
    
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return MovieResponse(
        id=db_movie.id,
        title=db_movie.title,
        release=db_movie.release,
        runtime=db_movie.runtime,
        synopsis=db_movie.synopsis,
        poster_url=db_movie.poster_url,
        created_at=db_movie.created_at,
        genres=[g.genre for g in db_movie.genres],
        tags=[t.tag for t in db_movie.tags]
    )


@router.delete("/{movie_id}", response_model=MessageResponse)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """Delete a movie"""
    repo = MovieRepository(db)
    
    if not repo.delete(movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return MessageResponse(message="Movie deleted successfully")


@router.get("/genre/{genre}", response_model=List[MovieResponse])
def get_movies_by_genre(
    genre: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get movies by genre"""
    repo = MovieRepository(db)
    movies = repo.get_by_genre(genre, limit=limit)
    
    return [
        MovieResponse(
            id=movie.id,
            title=movie.title,
            release=movie.release,
            runtime=movie.runtime,
            synopsis=movie.synopsis,
            poster_url=movie.poster_url,
            created_at=movie.created_at,
            genres=[g.genre for g in movie.genres],
            tags=[t.tag for t in movie.tags]
        )
        for movie in movies
    ]


@router.get("/popular/list", response_model=List[MovieResponse])
def get_popular_movies(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get popular movies (by review count)"""
    repo = MovieRepository(db)
    movies = repo.get_popular(limit=limit)
    
    return [
        MovieResponse(
            id=movie.id,
            title=movie.title,
            release=movie.release,
            runtime=movie.runtime,
            synopsis=movie.synopsis,
            poster_url=movie.poster_url,
            created_at=movie.created_at,
            genres=[g.genre for g in movie.genres],
            tags=[t.tag for t in movie.tags]
        )
        for movie in movies
    ]
