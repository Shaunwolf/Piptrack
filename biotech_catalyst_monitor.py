"""
Biotech Catalyst Monitor - Enhanced Phase 1 Feature
Monitors FDA calendars, clinical trial databases, and regulatory events
Addresses the backtesting recommendation for biotech-specific triggers
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
from dataclasses import dataclass

@dataclass
class CatalystEvent:
    """Data class for catalyst events"""
    symbol: str
    event_type: str
    date: datetime
    description: str
    importance: str
    phase: Optional[str] = None
    indication: Optional[str] = None

class BiotechCatalystMonitor:
    """Monitor biotech-specific catalysts and regulatory events"""
    
    def __init__(self):
        self.fda_calendar_events = []
        self.clinical_trial_events = []
        self.regulatory_events = []
        
        # Event importance scoring
        self.importance_weights = {
            'FDA Approval': 100,
            'FDA Advisory Committee': 90,
            'Phase 3 Results': 85,
            'PDUFA Date': 95,
            'Phase 2 Results': 70,
            'Phase 1 Results': 50,
            'Regulatory Filing': 60,
            'Partnership Announcement': 65,
            'Patent Expiration': 75,
            'Breakthrough Designation': 80
        }
    
    def scan_upcoming_catalysts(self, symbols: List[str] = None, days_ahead: int = 30) -> Dict:
        """Scan for upcoming biotech catalysts"""
        try:
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            # Get FDA calendar events
            fda_events = self._get_fda_calendar_events(end_date)
            
            # Get clinical trial milestones
            clinical_events = self._get_clinical_trial_events(symbols, end_date)
            
            # Get regulatory milestones
            regulatory_events = self._get_regulatory_events(symbols, end_date)
            
            # Combine and score events
            all_events = fda_events + clinical_events + regulatory_events
            
            # Filter by symbols if provided
            if symbols:
                all_events = [event for event in all_events if event.symbol.upper() in [s.upper() for s in symbols]]
            
            # Sort by importance and date
            all_events.sort(key=lambda x: (self.importance_weights.get(x.event_type, 0), x.date), reverse=True)
            
            return {
                'total_events': len(all_events),
                'high_impact_events': len([e for e in all_events if self.importance_weights.get(e.event_type, 0) >= 80]),
                'upcoming_events': [self._event_to_dict(event) for event in all_events[:20]],
                'catalyst_calendar': self._create_catalyst_calendar(all_events),
                'symbol_catalysts': self._group_by_symbol(all_events),
                'next_week_events': [self._event_to_dict(e) for e in all_events if e.date <= datetime.now() + timedelta(days=7)]
            }
            
        except Exception as e:
            logging.error(f"Error scanning biotech catalysts: {e}")
            return self._get_fallback_catalyst_data()
    
    def _get_fda_calendar_events(self, end_date: datetime) -> List[CatalystEvent]:
        """Get FDA calendar events (simulated - would use real FDA API)"""
        # This would connect to FDA Orange Book, Purple Book, and FDA Calendar APIs
        # For demonstration, using structured biotech catalyst data
        
        mock_fda_events = [
            CatalystEvent(
                symbol='NVAX',
                event_type='FDA Advisory Committee',
                date=datetime.now() + timedelta(days=14),
                description='FDA AdCom meeting for RSV vaccine',
                importance='High',
                phase='Commercial'
            ),
            CatalystEvent(
                symbol='MRNA',
                event_type='PDUFA Date',
                date=datetime.now() + timedelta(days=21),
                description='PDUFA date for RSV vaccine approval',
                importance='Critical',
                phase='Commercial'
            ),
            CatalystEvent(
                symbol='GILD',
                event_type='Phase 3 Results',
                date=datetime.now() + timedelta(days=28),
                description='Phase 3 data readout for hepatitis B cure',
                importance='High',
                phase='Phase 3'
            )
        ]
        
        return [event for event in mock_fda_events if event.date <= end_date]
    
    def _get_clinical_trial_events(self, symbols: List[str], end_date: datetime) -> List[CatalystEvent]:
        """Get clinical trial events from ClinicalTrials.gov"""
        # This would connect to ClinicalTrials.gov API
        
        mock_clinical_events = [
            CatalystEvent(
                symbol='SIGA',
                event_type='Phase 2 Results',
                date=datetime.now() + timedelta(days=18),
                description='Phase 2 results for TPOXX in additional indication',
                importance='Medium',
                phase='Phase 2',
                indication='Smallpox treatment'
            ),
            CatalystEvent(
                symbol='VKTX',
                event_type='Phase 1 Results',
                date=datetime.now() + timedelta(days=25),
                description='Phase 1 dose escalation results',
                importance='Medium',
                phase='Phase 1'
            )
        ]
        
        filtered_events = []
        if symbols:
            symbols_upper = [s.upper() for s in symbols]
            filtered_events = [event for event in mock_clinical_events 
                             if event.symbol.upper() in symbols_upper and event.date <= end_date]
        else:
            filtered_events = [event for event in mock_clinical_events if event.date <= end_date]
        
        return filtered_events
    
    def _get_regulatory_events(self, symbols: List[str], end_date: datetime) -> List[CatalystEvent]:
        """Get regulatory filing and patent events"""
        
        mock_regulatory_events = [
            CatalystEvent(
                symbol='ACAD',
                event_type='Regulatory Filing',
                date=datetime.now() + timedelta(days=12),
                description='BLA filing for Nuplazid expansion',
                importance='High',
                phase='Regulatory'
            ),
            CatalystEvent(
                symbol='PLUG',
                event_type='Partnership Announcement',
                date=datetime.now() + timedelta(days=35),
                description='Expected partnership announcement',
                importance='Medium',
                phase='Commercial'
            )
        ]
        
        filtered_events = []
        if symbols:
            symbols_upper = [s.upper() for s in symbols]
            filtered_events = [event for event in mock_regulatory_events 
                             if event.symbol.upper() in symbols_upper and event.date <= end_date]
        else:
            filtered_events = [event for event in mock_regulatory_events if event.date <= end_date]
        
        return filtered_events
    
    def analyze_catalyst_impact(self, symbol: str) -> Dict:
        """Analyze catalyst impact for specific symbol"""
        try:
            catalysts = self.scan_upcoming_catalysts([symbol])
            symbol_events = catalysts.get('symbol_catalysts', {}).get(symbol.upper(), [])
            
            if not symbol_events:
                return {
                    'symbol': symbol.upper(),
                    'catalyst_score': 0,
                    'next_catalyst': None,
                    'catalyst_count': 0,
                    'risk_level': 'Low',
                    'catalyst_timeline': []
                }
            
            # Calculate catalyst score
            total_score = sum(self.importance_weights.get(event['event_type'], 0) for event in symbol_events)
            avg_score = total_score / len(symbol_events) if symbol_events else 0
            
            # Get next catalyst
            sorted_events = sorted(symbol_events, key=lambda x: datetime.fromisoformat(x['date']))
            next_catalyst = sorted_events[0] if sorted_events else None
            
            # Determine risk level
            high_impact_events = [e for e in symbol_events if self.importance_weights.get(e['event_type'], 0) >= 80]
            if high_impact_events:
                risk_level = 'High'
            elif len(symbol_events) >= 2:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            return {
                'symbol': symbol.upper(),
                'catalyst_score': round(avg_score, 1),
                'next_catalyst': next_catalyst,
                'catalyst_count': len(symbol_events),
                'high_impact_count': len(high_impact_events),
                'risk_level': risk_level,
                'catalyst_timeline': sorted_events[:5]  # Next 5 catalysts
            }
            
        except Exception as e:
            logging.error(f"Error analyzing catalyst impact for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_catalyst_alerts(self, days_ahead: int = 7) -> List[Dict]:
        """Get catalyst alerts for the next week"""
        try:
            catalysts = self.scan_upcoming_catalysts(days_ahead=days_ahead)
            next_week_events = catalysts.get('next_week_events', [])
            
            alerts = []
            for event in next_week_events:
                importance_score = self.importance_weights.get(event['event_type'], 0)
                
                if importance_score >= 80:
                    alert_type = 'Critical'
                elif importance_score >= 60:
                    alert_type = 'High'
                else:
                    alert_type = 'Medium'
                
                alerts.append({
                    'symbol': event['symbol'],
                    'alert_type': alert_type,
                    'event_type': event['event_type'],
                    'date': event['date'],
                    'description': event['description'],
                    'days_until': (datetime.fromisoformat(event['date']) - datetime.now()).days,
                    'importance_score': importance_score
                })
            
            return sorted(alerts, key=lambda x: x['importance_score'], reverse=True)
            
        except Exception as e:
            logging.error(f"Error getting catalyst alerts: {e}")
            return []
    
    def _event_to_dict(self, event: CatalystEvent) -> Dict:
        """Convert CatalystEvent to dictionary"""
        return {
            'symbol': event.symbol,
            'event_type': event.event_type,
            'date': event.date.isoformat(),
            'description': event.description,
            'importance': event.importance,
            'phase': event.phase,
            'indication': event.indication,
            'importance_score': self.importance_weights.get(event.event_type, 0)
        }
    
    def _create_catalyst_calendar(self, events: List[CatalystEvent]) -> Dict:
        """Create catalyst calendar by date"""
        calendar = {}
        for event in events:
            date_key = event.date.strftime('%Y-%m-%d')
            if date_key not in calendar:
                calendar[date_key] = []
            calendar[date_key].append(self._event_to_dict(event))
        
        return calendar
    
    def _group_by_symbol(self, events: List[CatalystEvent]) -> Dict:
        """Group events by symbol"""
        symbol_groups = {}
        for event in events:
            if event.symbol not in symbol_groups:
                symbol_groups[event.symbol] = []
            symbol_groups[event.symbol].append(self._event_to_dict(event))
        
        return symbol_groups
    
    def _get_fallback_catalyst_data(self) -> Dict:
        """Provide fallback catalyst data when APIs unavailable"""
        return {
            'total_events': 0,
            'high_impact_events': 0,
            'upcoming_events': [],
            'catalyst_calendar': {},
            'symbol_catalysts': {},
            'next_week_events': [],
            'note': 'Using fallback data - connect to FDA and ClinicalTrials APIs for live data'
        }
    
    def get_biotech_watchlist(self) -> Dict:
        """Get biotech stocks with upcoming catalysts for watchlist"""
        try:
            catalysts = self.scan_upcoming_catalysts()
            symbol_catalysts = catalysts.get('symbol_catalysts', {})
            
            watchlist = []
            for symbol, events in symbol_catalysts.items():
                if events:
                    next_event = min(events, key=lambda x: datetime.fromisoformat(x['date']))
                    importance = self.importance_weights.get(next_event['event_type'], 0)
                    
                    watchlist.append({
                        'symbol': symbol,
                        'next_catalyst': next_event['event_type'],
                        'catalyst_date': next_event['date'],
                        'days_until': (datetime.fromisoformat(next_event['date']) - datetime.now()).days,
                        'importance_score': importance,
                        'description': next_event['description'],
                        'priority': 'High' if importance >= 80 else 'Medium' if importance >= 60 else 'Low'
                    })
            
            # Sort by importance and proximity
            watchlist.sort(key=lambda x: (x['importance_score'], -x['days_until']), reverse=True)
            
            return {
                'watchlist_count': len(watchlist),
                'high_priority_count': len([w for w in watchlist if w['priority'] == 'High']),
                'biotech_watchlist': watchlist[:15],  # Top 15 candidates
                'catalyst_summary': {
                    'next_week': len([w for w in watchlist if w['days_until'] <= 7]),
                    'next_month': len([w for w in watchlist if w['days_until'] <= 30]),
                    'high_impact': len([w for w in watchlist if w['importance_score'] >= 80])
                }
            }
            
        except Exception as e:
            logging.error(f"Error creating biotech watchlist: {e}")
            return {'error': str(e)}