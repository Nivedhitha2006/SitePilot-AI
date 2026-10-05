from sqlalchemy import Column,Integer,String,Float,Text,DateTime,Boolean,ForeignKey
from sqlalchemy.sql import func
from app.database.db import Base
class Website(Base):
    __tablename__='websites'; id=Column(Integer,primary_key=True); url=Column(String,unique=True,index=True); created_at=Column(DateTime,server_default=func.now())
class CrawlResult(Base):
    __tablename__='crawl_results'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); url=Column(String); status_code=Column(Integer); title=Column(String); meta_description=Column(Text); h1=Column(Integer); h2=Column(Integer); h3=Column(Integer); images=Column(Integer); missing_alt=Column(Integer); internal_links=Column(Integer); external_links=Column(Integer); broken_links=Column(Integer); canonical=Column(String); https=Column(Boolean); word_count=Column(Integer); response_ms=Column(Float); error=Column(Text)
class SEOResult(Base):
    __tablename__='seo_results'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); score=Column(Float); technical_score=Column(Float); content_score=Column(Float); issues_json=Column(Text)
class Keyword(Base):
    __tablename__='keywords'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); phrase=Column(String); count=Column(Integer); density=Column(Float)
class PerformanceResult(Base):
    __tablename__='performance_results'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); available=Column(Boolean); performance_score=Column(Float); lcp=Column(Float); cls=Column(Float); inp=Column(Float); raw_json=Column(Text); message=Column(Text)
class Recommendation(Base):
    __tablename__='recommendations'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); priority=Column(String); category=Column(String); issue=Column(String); explanation=Column(Text); solution=Column(Text); expected_impact=Column(String)
class AnalyticsData(Base):
    __tablename__='analytics_data'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); row_json=Column(Text)
class Lead(Base):
    __tablename__='leads'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); row_json=Column(Text)
class LeadPrediction(Base):
    __tablename__='lead_predictions'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); lead_key=Column(String); score=Column(Float); probability=Column(Float); intent=Column(String)
class Report(Base):
    __tablename__='reports'; id=Column(Integer,primary_key=True); website_id=Column(Integer,ForeignKey('websites.id')); path=Column(String); created_at=Column(DateTime,server_default=func.now())
