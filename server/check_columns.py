"""Script para verificar columnas de email_tasks"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres.thoxsxpfpdsjoykzahzv:maconiaso23982719827@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

async def check_columns():
    engine = create_async_engine(DB_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name='email_tasks' 
            ORDER BY ordinal_position
        """))
        
        print("\n📋 Columnas actuales de email_tasks:\n")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            print(f"  - {row[0]}: {row[1]} ({nullable})")
    
    await engine.dispose()

asyncio.run(check_columns())
