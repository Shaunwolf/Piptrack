#!/usr/bin/env python3
"""
Stock Scanner Monitoring Schedule
Automated scanning system with configurable intervals and alert thresholds
"""
import os
import time
import schedule
import logging
from datetime import datetime, timedelta
from threading import Thread
import json
from stock_scanner import StockScanner
from confidence_scorer import ConfidenceScorer
from app import app, db
from models import Stock, ScanResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScannerMonitor:
    def __init__(self):
        self.scanner = StockScanner()
        self.confidence_scorer = ConfidenceScorer()
        self.is_market_hours = self.check_market_hours()
        self.alert_threshold = 75  # High confidence threshold for alerts
        self.scan_count = 0
        
    def check_market_hours(self):
        """Check if current time is during market hours (9:30 AM - 4:00 PM EST)"""
        now = datetime.now()
        # Market hours: 9:30 AM to 4:00 PM EST, Monday to Friday
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return (now.weekday() < 5 and  # Monday to Friday
                market_open <= now <= market_close)
    
    def quick_scan(self):
        """Quick scan during market hours - 10 stocks every 5 minutes"""
        logger.info("Starting quick market hours scan")
        self.scan_count += 1
        
        try:
            with app.app_context():
                results = self.scanner.scan_stocks(max_results=10)
                high_confidence_stocks = [r for r in results if r.get('confidence_score', 0) >= self.alert_threshold]
                
                if high_confidence_stocks:
                    self.send_alerts(high_confidence_stocks, scan_type="quick")
                
                self.save_scan_results(results, "quick")
                logger.info(f"Quick scan #{self.scan_count} completed. Found {len(results)} stocks, {len(high_confidence_stocks)} high confidence")
                
        except Exception as e:
            logger.error(f"Quick scan failed: {e}")
    
    def comprehensive_scan(self):
        """Comprehensive scan - 50 stocks every 30 minutes"""
        logger.info("Starting comprehensive scan")
        
        try:
            with app.app_context():
                results = self.scanner.scan_stocks(max_results=50)
                high_confidence_stocks = [r for r in results if r.get('confidence_score', 0) >= 60]
                
                if high_confidence_stocks:
                    self.send_alerts(high_confidence_stocks, scan_type="comprehensive")
                
                self.save_scan_results(results, "comprehensive")
                logger.info(f"Comprehensive scan completed. Found {len(results)} stocks, {len(high_confidence_stocks)} above 60% confidence")
                
        except Exception as e:
            logger.error(f"Comprehensive scan failed: {e}")
    
    def after_hours_scan(self):
        """After hours scan - 20 stocks every hour for gap analysis"""
        logger.info("Starting after-hours gap analysis scan")
        
        try:
            with app.app_context():
                results = self.scanner.scan_stocks(max_results=20)
                gap_candidates = [r for r in results if r.get('confidence_score', 0) >= 50]
                
                if gap_candidates:
                    self.send_alerts(gap_candidates, scan_type="after_hours")
                
                self.save_scan_results(results, "after_hours")
                logger.info(f"After-hours scan completed. Found {len(gap_candidates)} gap candidates")
                
        except Exception as e:
            logger.error(f"After-hours scan failed: {e}")
    
    def save_scan_results(self, results, scan_type):
        """Save scan results to database"""
        try:
            for result in results[:10]:  # Save top 10 results
                scan_result = ScanResult(
                    symbol=result['symbol'],
                    price=result['price'],
                    confidence_score=result['confidence_score'],
                    rsi=result['rsi'],
                    volume_spike=result['volume_spike'],
                    pattern_type=result['pattern_type'],
                    scan_type=scan_type,
                    created_at=datetime.utcnow()
                )
                db.session.add(scan_result)
            
            db.session.commit()
            logger.info(f"Saved {len(results[:10])} scan results to database")
            
        except Exception as e:
            logger.error(f"Error saving scan results: {e}")
            db.session.rollback()
    
    def send_alerts(self, stocks, scan_type):
        """Send alerts for high confidence stocks"""
        alert_message = f"🔥 {scan_type.upper()} SCAN ALERT 🔥\n"
        alert_message += f"Found {len(stocks)} high-confidence opportunities:\n\n"
        
        for stock in stocks[:5]:  # Top 5 alerts
            alert_message += f"📈 {stock['symbol']}: ${stock['price']} "
            alert_message += f"(Confidence: {stock['confidence_score']}%)\n"
            alert_message += f"   Pattern: {stock['pattern_type']}, RSI: {stock['rsi']}\n\n"
        
        logger.info(f"ALERT: {alert_message}")
        
        # Here you could add email/SMS/Discord notifications
        # For now, we'll just log the alerts
    
    def setup_schedule(self):
        """Setup scanning schedule based on market hours"""
        # Market hours schedule (9:30 AM - 4:00 PM EST)
        schedule.every(5).minutes.do(self.quick_scan).tag('market_hours')
        schedule.every(30).minutes.do(self.comprehensive_scan).tag('market_hours')
        
        # After hours schedule
        schedule.every().hour.do(self.after_hours_scan).tag('after_hours')
        
        # Daily summary at market close
        schedule.every().day.at("16:05").do(self.daily_summary)
        
        # Weekly deep scan on Sunday
        schedule.every().sunday.at("08:00").do(self.weekly_deep_scan)
        
        logger.info("Scanner schedule configured:")
        logger.info("  - Quick scans: Every 5 minutes during market hours")
        logger.info("  - Comprehensive scans: Every 30 minutes during market hours")
        logger.info("  - After-hours scans: Every hour")
        logger.info("  - Daily summary: 4:05 PM EST")
        logger.info("  - Weekly deep scan: Sunday 8:00 AM")
    
    def daily_summary(self):
        """Generate daily summary of scan results"""
        logger.info("Generating daily summary")
        
        try:
            with app.app_context():
                today = datetime.utcnow().date()
                daily_results = ScanResult.query.filter(
                    ScanResult.created_at >= today
                ).all()
                
                if daily_results:
                    top_stocks = {}
                    for result in daily_results:
                        if result.symbol not in top_stocks or result.confidence_score > top_stocks[result.symbol]:
                            top_stocks[result.symbol] = result.confidence_score
                    
                    sorted_stocks = sorted(top_stocks.items(), key=lambda x: x[1], reverse=True)
                    
                    summary = f"📊 DAILY SUMMARY - {today}\n"
                    summary += f"Total scans: {len(daily_results)}\n"
                    summary += f"Unique stocks analyzed: {len(top_stocks)}\n"
                    summary += f"Top 5 performers:\n"
                    
                    for symbol, confidence in sorted_stocks[:5]:
                        summary += f"  {symbol}: {confidence}% confidence\n"
                    
                    logger.info(summary)
                
        except Exception as e:
            logger.error(f"Daily summary failed: {e}")
    
    def weekly_deep_scan(self):
        """Weekly comprehensive analysis of all tracked stocks"""
        logger.info("Starting weekly deep scan")
        
        try:
            with app.app_context():
                results = self.scanner.scan_stocks(max_results=100)
                logger.info(f"Weekly deep scan completed. Analyzed {len(results)} stocks")
                
        except Exception as e:
            logger.error(f"Weekly deep scan failed: {e}")
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while True:
            try:
                # Update market hours status
                self.is_market_hours = self.check_market_hours()
                
                # Clear inappropriate schedules
                if self.is_market_hours:
                    schedule.clear('after_hours')
                    # Re-add market hours schedules if needed
                    if not schedule.get_jobs('market_hours'):
                        schedule.every(5).minutes.do(self.quick_scan).tag('market_hours')
                        schedule.every(30).minutes.do(self.comprehensive_scan).tag('market_hours')
                else:
                    schedule.clear('market_hours')
                    # Re-add after hours schedule if needed
                    if not schedule.get_jobs('after_hours'):
                        schedule.every().hour.do(self.after_hours_scan).tag('after_hours')
                
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

def start_monitor():
    """Start the scanner monitor"""
    monitor = ScannerMonitor()
    monitor.setup_schedule()
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=monitor.run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Stock Scanner Monitor started successfully")
    return monitor

if __name__ == "__main__":
    monitor = start_monitor()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(3600)  # Sleep for 1 hour
    except KeyboardInterrupt:
        logger.info("Scanner monitor stopped by user")