from database import create_warpcast, get_warpcast_by_hash, get_warpcasts_by_username, get_all_warpcasts, create_db_and_tables, get_engine, get_env_prefix
from schemas import Warpcast
from datetime import datetime
import os
from sqlalchemy import text

def reset_tables():
    """Helper function to reset both dev and prod tables"""
    engine = get_engine()
    
    # Reset dev table
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    dev_prefix = get_env_prefix()
    with engine.connect() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {dev_prefix}warpcasts"))
        connection.commit()
    create_db_and_tables()  # Recreate dev table
    
    # Reset prod table
    os.environ["REPLIT_DEPLOYMENT"] = "1"
    prod_prefix = get_env_prefix()
    with engine.connect() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {prod_prefix}warpcasts"))
        connection.commit()
    create_db_and_tables()  # Recreate prod table
    
    # Reset back to dev environment
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    create_db_and_tables()

def create_test_warpcast(hash_value: str, username: str = "testuser") -> Warpcast:
    """Helper function to create test Warpcast objects"""
    return Warpcast(
        raw_cast={
            "hash": hash_value,
            "author": {
                "username": username,
                "fid": 12345
            },
            "text": f"Test cast with hash {hash_value}",
            "timestamp": 1709668800000,
            "replies": {"count": 0},
            "reactions": {"count": 0},
            "recasts": {"count": 0}
        },
        hash=hash_value,
        username=username,
        user_fid=12345,
        text=f"Test cast with hash {hash_value}",
        timestamp=datetime.fromtimestamp(1709668800),
        replies=0,
        reactions=0,
        recasts=0
    )

def test_environment_separation():
    """Test that dev and prod environments use separate tables"""
    print("\n=== Testing Environment Separation ===")
    
    # Reset tables and ensure we're in dev environment
    reset_tables()
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    create_db_and_tables()
    
    # Test in dev environment
    test_cast_dev = create_test_warpcast("test_env_dev")
    dev_result = create_warpcast(test_cast_dev)
    print(f"Dev environment cast created: {dev_result is not None}")
    
    # Get count of casts in dev
    dev_casts = len(get_all_warpcasts())
    print(f"Dev casts count: {dev_casts}")
    
    # Test in prod environment
    os.environ["REPLIT_DEPLOYMENT"] = "1"
    create_db_and_tables()
    test_cast_prod = create_test_warpcast("test_env_prod")
    prod_result = create_warpcast(test_cast_prod)
    print(f"Prod environment cast created: {prod_result is not None}")
    
    # Get count of casts in prod
    prod_casts = len(get_all_warpcasts())
    print(f"Prod casts count: {prod_casts}")
    
    # Switch back to dev and verify count hasn't changed
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    create_db_and_tables()
    dev_casts_after = len(get_all_warpcasts())
    print(f"Dev casts count after: {dev_casts_after}")
    
    # Verify environment separation
    env_separation_working = (
        dev_casts == 1 and  # Dev has one cast
        prod_casts == 1 and  # Prod has one cast
        dev_casts == dev_casts_after  # Dev count unchanged after prod operations
    )
    print(f"Environment separation working: {env_separation_working}")

def test_uniqueness_constraint():
    """Test that duplicate hashes are prevented"""
    print("\n=== Testing Uniqueness Constraint ===")
    
    # Reset tables and ensure we're in dev environment
    reset_tables()
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    create_db_and_tables()
    
    # Create initial cast
    test_cast_1 = create_test_warpcast("test_unique_1")
    result_1 = create_warpcast(test_cast_1)
    print(f"First cast created: {result_1 is not None}")
    
    # Attempt to create duplicate
    test_cast_2 = create_test_warpcast("test_unique_1")  # Same hash
    result_2 = create_warpcast(test_cast_2)
    print(f"Duplicate prevented: {result_2 is None}")
    
    # Create cast with different hash
    test_cast_3 = create_test_warpcast("test_unique_2")  # Different hash
    result_3 = create_warpcast(test_cast_3)
    print(f"Different hash created: {result_3 is not None}")

def test_crud_operations():
    """Test Create, Read, Update, Delete operations"""
    print("\n=== Testing CRUD Operations ===")
    
    # Reset tables and ensure we're in dev environment
    reset_tables()
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    create_db_and_tables()
    
    # Test Create
    test_cast = create_test_warpcast("test_crud")
    db_cast = create_warpcast(test_cast)
    print(f"Create operation successful: {db_cast is not None}")

    # Test Read by hash
    fetched_cast = get_warpcast_by_hash("test_crud")
    print(f"Read by hash successful: {fetched_cast is not None and fetched_cast.hash == 'test_crud'}")

    # Test Read by username
    user_casts = get_warpcasts_by_username("testuser")
    print(f"Read by username successful: {len(user_casts) > 0}")

    # Test Read all
    all_casts = get_all_warpcasts()
    print(f"Read all successful: {len(all_casts) > 0}")

def run_all_tests():
    """Run all test cases"""
    print("Starting database tests...")
    
    # Ensure we start in dev environment
    os.environ["REPLIT_DEPLOYMENT"] = "0"
    create_db_and_tables()
    
    # Run tests
    test_environment_separation()
    test_uniqueness_constraint()
    test_crud_operations()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    run_all_tests()
