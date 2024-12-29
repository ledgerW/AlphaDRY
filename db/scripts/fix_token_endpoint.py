from database import get_session
from sqlalchemy import func, text
from db.models.token import TokenDB
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/token/{address}")
async def get_token(address: str):
    """Get detailed information about a specific token including all relationships."""
    try:
        with get_session() as session:
            # Query prod_tokens table directly with SQL to ensure we're using the right table
            # Use chain-specific address matching
            result = session.execute(text("""
                SELECT id, symbol, name, chain, address 
                FROM prod_tokens 
                WHERE 
                    CASE 
                        WHEN address LIKE '0x%' THEN LOWER(address) = LOWER(:address)
                        ELSE address = :address
                    END
            """), {'address': address}).first()
            
            if result:
                print(f"Found token: ID={result.id}, Symbol={result.symbol}, Address={result.address}")
            else:
                print(f"No token found for address: {address}")
            
            return result
            
    except Exception as e:
        print(f"Error querying token: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the endpoint with some known addresses from the prod data
    import asyncio
    
    async def test_addresses():
        # Test with different cases of known prod addresses
        addresses = [
            # Test Base token addresses (should be case-insensitive)
            "0x1751be7F73DB14e7E9d26e00B647D79F894Ebb21",  # SWORDS token
            "0x1751be7f73db14e7e9d26e00b647d79f894ebb21",  # Same in lowercase
            "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",  # DEGEN token
            "0x4ED4E862860BED51A9570B96D89AF5E1B0EFEFED",  # Same in uppercase
            
            # Test Solana token addresses (should be case-sensitive)
            "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",  # RAY token - correct case
            "4K3DYJZVZP8EMZWUXBBCJEVWSKKK59S5ICNLY3QRKX6R",  # Wrong case - should not match
            "LoL1RDQiUfifC2BX28xaef6r2G8ES8SEzgrzThJemMv",  # LOL token - correct case
            "lol1rdqiufifc2bx28xaef6r2g8es8segrzthjemMv"    # Wrong case - should not match
        ]
        
        for addr in addresses:
            print(f"\nTesting address: {addr}")
            result = await get_token(addr)
            if result:
                print("Success!")
            else:
                print("Not found")
    
    asyncio.run(test_addresses())
