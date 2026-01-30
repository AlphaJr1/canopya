"""
Gamification Logic untuk User Interactions
Handle user actions dan generate alerts dengan context

"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GamificationEngine:
    """Gamification Engine untuk user interactions"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize gamification engine dengan config file"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.actions_config = self.config['gamification']['actions']
        self.alert_thresholds = self.config['gamification']['alert_thresholds']
        self.alert_cooldown_minutes = self.config['whatsapp']['alert_cooldown_minutes']
        
        self.last_alert_times = {}
        
    
    def validate_action(self, action_type: str, current_state: Dict) -> Dict:
        """
        Validate apakah action valid untuk dilakukan
        Args:
            action_type: Tipe action (add_nutrient, add_water, dll)
            current_state: Dict dengan keys: ph, tds, status
        Returns:
            Dict dengan keys: valid (bool), reason (str), warning (str)
        """
        if action_type not in self.actions_config:
            return {
                'valid': False,
                'reason': f'Action tidak dikenal: {action_type}'
            }
        
        ph = current_state['ph']
        tds = current_state['tds']
        
        warnings = []
        
        # Validate berdasarkan action type
        if action_type == 'add_nutrient':
            if tds > self.alert_thresholds['tds_critical_high']:
                return {
                    'valid': False,
                    'reason': f'TDS sudah terlalu tinggi ({tds} ppm). Tidak bisa tambah nutrisi.'
                }
            elif tds > 1400:
                warnings.append(f'TDS sudah di atas optimal ({tds} ppm). Pertimbangkan tambah air sebagai gantinya.')
        
        elif action_type == 'add_water':
            if tds < self.alert_thresholds['tds_critical_low']:
                return {
                    'valid': False,
                    'reason': f'TDS sudah terlalu rendah ({tds} ppm). Tidak bisa tambah air.'
                }
            elif tds < 800:
                warnings.append(f'TDS sudah di bawah optimal ({tds} ppm). Pertimbangkan tambah nutrisi sebagai gantinya.')
        
        elif action_type == 'add_ph_down':
            if ph < self.alert_thresholds['ph_critical_low']:
                return {
                    'valid': False,
                    'reason': f'pH sudah terlalu rendah ({ph}). Tidak bisa tambah pH down.'
                }
            elif ph < 5.5:
                warnings.append(f'pH sudah di bawah optimal ({ph}). Pertimbangkan tambah pH up sebagai gantinya.')
        
        elif action_type == 'add_ph_up':
            if ph > self.alert_thresholds['ph_critical_high']:
                return {
                    'valid': False,
                    'reason': f'pH sudah terlalu tinggi ({ph}). Tidak bisa tambah pH up.'
                }
            elif ph > 6.5:
                warnings.append(f'pH sudah di atas optimal ({ph}). Pertimbangkan tambah pH down sebagai gantinya.')
        
        result = {'valid': True}
        if warnings:
            result['warning'] = ' '.join(warnings)
        
        return result
    
    def calculate_action_effect(self, action_type: str, amount: float = 1.0) -> Dict:
        """
        Calculate efek dari action
        Args:
            action_type: Tipe action
            amount: Multiplier (default 1.0)
        Returns:
            Dict dengan keys: ph_change, tds_change
        """
        action = self.actions_config[action_type]
        
        return {
            'ph_change': action['ph_change'] * amount,
            'tds_change': action['tds_change'] * amount
        }
    
    def check_improvement(self, before_status: str, after_status: str) -> bool:
        """
        Check apakah action membuat status lebih baik
        Args:
            before_status: Status sebelum action
            after_status: Status setelah action
        Returns:
            True jika improved
        """
        status_ranking = {
            'critical': 0,
            'warning': 1,
            'optimal': 2
        }
        
        before_rank = status_ranking.get(before_status, 0)
        after_rank = status_ranking.get(after_status, 0)
        
        return after_rank > before_rank
    
    def should_send_alert(self, alert_type: str) -> bool:
        """
        Check apakah alert boleh dikirim (cooldown check)
        Args:
            alert_type: Tipe alert
        Returns:
            True jika boleh kirim
        """
        if alert_type not in self.last_alert_times:
            return True
        
        last_time = self.last_alert_times[alert_type]
        time_since_last = datetime.now() - last_time
        
        return time_since_last > timedelta(minutes=self.alert_cooldown_minutes)
    
    def mark_alert_sent(self, alert_type: str):
        self.last_alert_times[alert_type] = datetime.now()
    
    def generate_alert_message(self, alert: Dict, include_buttons: bool = True) -> Dict:
        """
        Generate alert message untuk WhatsApp
        Args:
            alert: Dict dari insights dengan keys: type, severity, message, recommended_action
            include_buttons: Apakah include interactive buttons
        Returns:
            Dict dengan keys: message, buttons (optional)
        """
        severity_emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        emoji = severity_emoji.get(alert['severity'], 'ℹ️')
        
        # Build message
        message_parts = [
            f"{emoji} *Alert: {alert['message']}*",
            ""
        ]
        
        # Add recommendation if available
        if alert.get('recommended_action'):
            action_labels = {
                'add_nutrient': 'Tambah Nutrisi',
                'add_water': 'Tambah Air',
                'add_ph_down': 'Tambah pH Down (Asam)',
                'add_ph_up': 'Tambah pH Up (Basa)',
                'monitor': 'Monitor Terus'
            }
            action_label = action_labels.get(alert['recommended_action'], alert['recommended_action'])
            message_parts.append(f"💡 Rekomendasi: {action_label}")
        
        message = "\n".join(message_parts)
        
        result = {'message': message}
        
        # Add buttons if requested
        if include_buttons and alert.get('recommended_action') and alert['recommended_action'] != 'monitor':
            result['buttons'] = [
                {
                    'id': f"action_{alert['recommended_action']}",
                    'text': action_labels.get(alert['recommended_action'], 'Lakukan')
                },
                {
                    'id': 'action_check_guide',
                    'text': '📖 Cek Panduan'
                },
                {
                    'id': 'action_ignore',
                    'text': '❌ Abaikan'
                }
            ]
        
        return result
    
    def generate_achievement_message(self, stats: Dict) -> Optional[str]:
        """
        Generate achievement message berdasarkan stats
        Args:
            stats: Dict dari get_action_stats()
        Returns:
            Achievement message atau None
        """
        achievements = []
        
        total_actions = stats.get('total_actions', 0)
        success_rate = stats.get('success_rate', 0)
        
        # Achievement milestones
        if total_actions == 1:
            achievements.append("🎉 *First Action!* Kamu baru saja melakukan aksi pertama untuk tanaman kamu!")
        elif total_actions == 10:
            achievements.append("🏆 *10 Actions!* Kamu sudah melakukan 10 aksi. Keep it up!")
        elif total_actions == 50:
            achievements.append("🌟 *50 Actions!* Wow, kamu sangat aktif merawat tanaman!")
        elif total_actions == 100:
            achievements.append("💯 *Century!* 100 aksi! Kamu adalah master hidroponik!")
        
        # Success rate achievements
        if total_actions >= 10:
            if success_rate >= 0.9:
                achievements.append("🎯 *Expert!* 90%+ aksi kamu berhasil meningkatkan kondisi tanaman!")
            elif success_rate >= 0.75:
                achievements.append("👍 *Good Job!* 75%+ aksi kamu efektif!")
        
        if achievements:
            return "\n".join(achievements)
        
        return None
    
    def format_action_summary(self, action_data: Dict) -> str:
        """
        Format action summary untuk display
        Args:
            action_data: Dict dengan before/after values
        Returns:
            Formatted string
        """
        action_labels = {
            'add_nutrient': 'Menambah Nutrisi',
            'add_water': 'Menambah Air',
            'add_ph_down': 'Menambah pH Down',
            'add_ph_up': 'Menambah pH Up'
        }
        
        action_label = action_labels.get(action_data['action_type'], action_data['action_type'])
        
        summary_parts = [
            f"✅ *{action_label}*",
            "",
            f"pH: {action_data['ph_before']:.2f} → {action_data['ph_after']:.2f}",
            f"TDS: {action_data['tds_before']:.0f} → {action_data['tds_after']:.0f} ppm"
        ]
        
        if action_data.get('improved_status'):
            summary_parts.append("")
            summary_parts.append("🎉 Kondisi tanaman membaik!")
        
        return "\n".join(summary_parts)

if __name__ == "__main__":
    # Test gamification engine
    logging.basicConfig(level=logging.INFO)
    
    engine = GamificationEngine()
    
    print("Testing Gamification Engine...")
    
    # Test validate action
    print("\n1. Testing action validation...")
    current_state = {'ph': 7.2, 'tds': 1200, 'status': 'warning'}
    
    validation = engine.validate_action('add_ph_down', current_state)
    print(f"add_ph_down validation: {validation}")
    
    validation = engine.validate_action('add_nutrient', current_state)
    print(f"add_nutrient validation: {validation}")
    
    # Test calculate effect
    print("\n2. Testing effect calculation...")
    effect = engine.calculate_action_effect('add_ph_down')
    print(f"add_ph_down effect: {effect}")
    
    # Test alert message generation
    print("\n3. Testing alert message generation...")
    alert = {
        'type': 'ph_high',
        'severity': 'warning',
        'message': 'pH terlalu tinggi (7.2). Target: 5.5-6.5',
        'recommended_action': 'add_ph_down'
    }
    alert_msg = engine.generate_alert_message(alert)
    print(f"Alert message:\n{alert_msg['message']}")
    print(f"Buttons: {alert_msg.get('buttons')}")
    
    # Test action summary
    print("\n4. Testing action summary...")
    action_data = {
        'action_type': 'add_ph_down',
        'ph_before': 7.2,
        'ph_after': 6.5,
        'tds_before': 1200,
        'tds_after': 1210,
        'improved_status': True
    }
    summary = engine.format_action_summary(action_data)
    print(f"Action summary:\n{summary}")
    
    print("\nGamification engine test complete!")
