#!/usr/bin/env python3
from sqlalchemy.engine.url import make_url

def test_url():
    test_cases = [
        "secret:DATABASE_URL",
        "postgresql://user:password@localhost:5432/dbname",
        "sqlite:///./test.db"
    ]
    
    for url in test_cases:
        print("=" * 50)
        print(f"Testing: {repr(url)}")
        
        try:
            parsed = make_url(url)
            print(f"✅ Success:")
            print(f"   Driver: {parsed.drivername}")
            if parsed.host:
                print(f"   Host: {parsed.host}")
            if parsed.port:
                print(f"   Port: {parsed.port}")
            if parsed.database:
                print(f"   Database: {parsed.database}")
            if parsed.username:
                print(f"   User: {parsed.username}")
            if parsed.password:
                print(f"   Password: {'*' * len(parsed.password)}")
                
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_url()