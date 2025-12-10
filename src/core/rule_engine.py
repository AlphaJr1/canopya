"""
Rule-Based Engine for NFT Hydroponic Sensor Diagnostics
Handles sensor data analysis with threshold-based rules

"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Severity(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"

class GrowthStage(Enum):
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FRUITING = "fruiting"

@dataclass
class SensorReading:
    """
    """
    ph: Optional[float] = None
    tds: Optional[float] = None  # ppm
    temperature: Optional[float] = None  # Celsius
    humidity: Optional[float] = None  # percentage
    growth_stage: GrowthStage = GrowthStage.VEGETATIVE

@dataclass
class Diagnostic:
    """
    severity: Severity
    parameter: str
    value: float
    issue: str
    action: str
    optimal_range: str

class RuleBasedEngine:
    
    # Validated thresholds from research (see research_sources.md)
    """
    THRESHOLDS = {
        'ph': {
            'optimal': (5.5, 6.5),
            'warning': (5.0, 7.0),
            'critical': (4.5, 7.5),
        },
        'tds': {
            'seedling': {
                'optimal': (500, 1000),
                'warning': (400, 1200),
                'critical': (300, 1500),
            },
            'vegetative': {
                'optimal': (800, 1200),
                'warning': (600, 1400),
                'critical': (500, 1600),
            },
            'fruiting': {
                'optimal': (1000, 1500),
                'warning': (800, 1700),
                'critical': (700, 2000),
            },
        },
        'temperature': {
            'optimal': (18, 24),
            'warning': (16, 26),
            'critical': (14, 30),
        },
        'humidity': {
            'optimal': (50, 70),
            'warning': (40, 80),
            'critical': (30, 90),
        },
    }
    
    def diagnose_ph(self, ph: float) -> Optional[Diagnostic]:
        """
        """
        if ph < 4.5 or ph > 7.5:
            return Diagnostic(
                severity=Severity.CRITICAL,
                parameter="pH",
                value=ph,
                issue=f"pH CRITICAL: {ph} (sangat di luar range optimal)",
                action="🚨 SEGERA sesuaikan pH! Tambahkan pH UP/DOWN solution secara bertahap. Target: 5.5-6.5",
                optimal_range="5.5-6.5"
            )
        elif ph < 5.0 or ph > 7.0:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="pH",
                value=ph,
                issue=f"pH Warning: {ph} (mendekati batas tidak optimal)",
                action="⚠️ Sesuaikan pH ke range 5.5-6.5. Monitor setiap hari.",
                optimal_range="5.5-6.5"
            )
        elif 5.5 <= ph <= 6.5:
            return Diagnostic(
                severity=Severity.NORMAL,
                parameter="pH",
                value=ph,
                issue=f"✅ pH Normal: {ph}",
                action="Pertahankan level ini. Monitor rutin 2-3 hari sekali.",
                optimal_range="5.5-6.5"
            )
        else:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="pH",
                value=ph,
                issue=f"pH: {ph} (di ujung range optimal)",
                action="Monitor lebih ketat dan bersiap untuk adjustment.",
                optimal_range="5.5-6.5"
            )
    
    def diagnose_tds(self, tds: float, growth_stage: GrowthStage) -> Optional[Diagnostic]:
        stage_name = growth_stage.value
        thresholds = self.THRESHOLDS['tds'][stage_name]
        
        min_opt, max_opt = thresholds['optimal']
        min_warn, max_warn = thresholds['warning']
        min_crit, max_crit = thresholds['critical']
        
        if tds < min_crit or tds > max_crit:
            if tds < min_crit:
                return Diagnostic(
                    severity=Severity.CRITICAL,
                    parameter="TDS",
                    value=tds,
                    issue=f"TDS CRITICAL rendah: {tds} ppm (target: {min_opt}-{max_opt} ppm untuk {stage_name})",
                    action=f"🚨 SEGERA tambahkan nutrisi! Target: {min_opt}-{max_opt} ppm. Tambahkan nutrisi A+B sesuai dosis.",
                    optimal_range=f"{min_opt}-{max_opt} ppm"
                )
            else:
                return Diagnostic(
                    severity=Severity.CRITICAL,
                    parameter="TDS",
                    value=tds,
                    issue=f"TDS CRITICAL tinggi: {tds} ppm (target: {min_opt}-{max_opt} ppm untuk {stage_name})",
                    action=f"🚨 SEGERA encerkan! Tambahkan air bersih bertahap. Risiko: nutrient burn. Target: {min_opt}-{max_opt} ppm.",
                    optimal_range=f"{min_opt}-{max_opt} ppm"
                )
        
        elif tds < min_warn or tds > max_warn:
            if tds < min_warn:
                return Diagnostic(
                    severity=Severity.WARNING,
                    parameter="TDS",
                    value=tds,
                    issue=f"TDS Warning rendah: {tds} ppm (target: {min_opt}-{max_opt} ppm)",
                    action=f"➕ Tambahkan nutrisi secara bertahap hingga {min_opt}-{max_opt} ppm. Monitor harian.",
                    optimal_range=f"{min_opt}-{max_opt} ppm"
                )
            else:
                return Diagnostic(
                    severity=Severity.WARNING,
                    parameter="TDS",
                    value=tds,
                    issue=f"TDS Warning tinggi: {tds} ppm (target: {min_opt}-{max_opt} ppm)",
                    action=f"💧 Encerkan dengan air bersih hingga {min_opt}-{max_opt} ppm. Monitor harian.",
                    optimal_range=f"{min_opt}-{max_opt} ppm"
                )
        
        elif min_opt <= tds <= max_opt:
            return Diagnostic(
                severity=Severity.NORMAL,
                parameter="TDS",
                value=tds,
                issue=f"✅ TDS Normal: {tds} ppm (optimal untuk {stage_name})",
                action="Pertahankan level ini. Monitor rutin.",
                optimal_range=f"{min_opt}-{max_opt} ppm"
            )
        else:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="TDS",
                value=tds,
                issue=f"TDS: {tds} ppm (di ujung range optimal)",
                action="Monitor lebih ketat.",
                optimal_range=f"{min_opt}-{max_opt} ppm"
            )
    
    def diagnose_temperature(self, temp: float) -> Optional[Diagnostic]:
        """
        """
        if temp < 14 or temp > 30:
            return Diagnostic(
                severity=Severity.CRITICAL,
                parameter="Temperature",
                value=temp,
                issue=f"Suhu CRITICAL: {temp}°C (target: 18-24°C)",
                action="🚨 SEGERA sesuaikan suhu! Gunakan heater (jika <14°C) atau chiller/fan (jika >30°C). Suhu ekstrem dapat merusak tanaman.",
                optimal_range="18-24°C"
            )
        elif temp < 16 or temp > 26:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="Temperature",
                value=temp,
                issue=f"Suhu Warning: {temp}°C (target: 18-24°C)",
                action="🌡️ Sesuaikan suhu ruangan/greenhouse. Pastikan ventilasi baik.",
                optimal_range="18-24°C"
            )
        elif 18 <= temp <= 24:
            return Diagnostic(
                severity=Severity.NORMAL,
                parameter="Temperature",
                value=temp,
                issue=f"✅ Suhu Normal: {temp}°C",
                action="Pertahankan suhu ini. Ideal untuk pertumbuhan.",
                optimal_range="18-24°C"
            )
        else:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="Temperature",
                value=temp,
                issue=f"Suhu: {temp}°C (acceptable tapi tidak optimal)",
                action="Monitor suhu lebih ketat.",
                optimal_range="18-24°C"
            )
    
    def diagnose_humidity(self, humidity: float) -> Optional[Diagnostic]:
        """
        """
        if humidity < 30 or humidity > 90:
            return Diagnostic(
                severity=Severity.CRITICAL,
                parameter="Humidity",
                value=humidity,
                issue=f"Kelembapan CRITICAL: {humidity}% (target: 50-70%)",
                action="🚨 SEGERA sesuaikan kelembapan! Gunakan humidifier (jika <30%) atau dehumidifier/ventilasi (jika >90%).",
                optimal_range="50-70%"
            )
        elif humidity < 40 or humidity > 80:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="Humidity",
                value=humidity,
                issue=f"Kelembapan Warning: {humidity}% (target: 50-70%)",
                action="💨 Sesuaikan kelembapan dengan ventilasi/humidifier sesuai kebutuhan.",
                optimal_range="50-70%"
            )
        elif 50 <= humidity <= 70:
            return Diagnostic(
                severity=Severity.NORMAL,
                parameter="Humidity",
                value=humidity,
                issue=f"✅ Kelembapan Normal: {humidity}%",
                action="Pertahankan level ini.",
                optimal_range="50-70%"
            )
        else:
            return Diagnostic(
                severity=Severity.WARNING,
                parameter="Humidity",
                value=humidity,
                issue=f"Kelembapan: {humidity}% (acceptable)",
                action="Monitor kelembapan.",
                optimal_range="50-70%"
            )
    
    def diagnose_all(self, sensor_data: SensorReading, rag_context: Optional[str] = None) -> Dict:
        """
        Run complete diagnosis on all sensor readings
        
        Args:
            sensor_data: SensorReading object with sensor values
            rag_context: Optional knowledge context from RAG for enriched responses
            
        Returns:
            Complete diagnostic report with optional RAG-enhanced insights
        logger.info(f"Running diagnostics on sensor data: {sensor_data}")
        
        """
        diagnostics = []
        severity_levels = []
        
        # Diagnose each parameter
        if sensor_data.ph is not None:
            diag = self.diagnose_ph(sensor_data.ph)
            if diag:
                diagnostics.append(diag)
                severity_levels.append(diag.severity)
        
        if sensor_data.tds is not None:
            diag = self.diagnose_tds(sensor_data.tds, sensor_data.growth_stage)
            if diag:
                diagnostics.append(diag)
                severity_levels.append(diag.severity)
        
        if sensor_data.temperature is not None:
            diag = self.diagnose_temperature(sensor_data.temperature)
            if diag:
                diagnostics.append(diag)
                severity_levels.append(diag.severity)
        
        if sensor_data.humidity is not None:
            diag = self.diagnose_humidity(sensor_data.humidity)
            if diag:
                diagnostics.append(diag)
                severity_levels.append(diag.severity)
        
        # Determine overall severity
        if Severity.CRITICAL in severity_levels:
            overall_severity = Severity.CRITICAL
        elif Severity.WARNING in severity_levels:
            overall_severity = Severity.WARNING
        else:
            overall_severity = Severity.NORMAL
        
        # Format report
        report = {
            'overall_severity': overall_severity.value,
            'diagnostics': [
                {
                    'severity': d.severity.value,
                    'parameter': d.parameter,
                    'value': d.value,
                    'issue': d.issue,
                    'action': d.action,
                    'optimal_range': d.optimal_range
                }
                for d in diagnostics
            ],
            'summary': self._generate_summary(overall_severity, diagnostics, rag_context),
            'has_rag_context': rag_context is not None,
            'rag_context': rag_context if rag_context else None
        }
        
        return report
    
    def _generate_summary(self, severity: Severity, diagnostics: List[Diagnostic], rag_context: Optional[str] = None) -> str:
        # Base summary (more natural language)
        if severity == Severity.CRITICAL:
            critical_params = [d.parameter for d in diagnostics if d.severity == Severity.CRITICAL]
            params_str = ' dan '.join(critical_params) if len(critical_params) <= 2 else ', '.join(critical_params[:-1]) + ', dan ' + critical_params[-1]
            base = f"Wah, ada masalah serius nih! {params_str} kamu berada di level kritis. Ini perlu ditangani segera ya, kalau dibiarkan bisa merusak tanaman."
        elif severity == Severity.WARNING:
            warning_params = [d.parameter for d in diagnostics if d.severity == Severity.WARNING]
            params_str = ' dan '.join(warning_params) if len(warning_params) <= 2 else ', '.join(warning_params[:-1]) + ', dan ' + warning_params[-1]
            base = f"Ada beberapa parameter yang perlu diperhatikan: {params_str}."
        else:
            base = "Bagus! Semua parameter dalam kondisi optimal. Sistem kamu berjalan dengan baik, tinggal monitor rutin aja."
        
        return base

if __name__ == "__main__":
    
    print("Rule-Based Engine Test\n")
    
    engine = RuleBasedEngine()
    
    scenarios = [
        {
            'name': "Normal Conditions",
            'data': SensorReading(ph=6.0, tds=900, temperature=22, humidity=60)
        },
        {
            'name': "Critical pH",
            'data': SensorReading(ph=4.0, tds=1000, temperature=22, humidity=60)
        },
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        
        report = engine.diagnose_all(scenario['data'])
        
        print(f"Overall: {report['summary']}\n")
        for diag in report['diagnostics']:
            print(f"{diag['parameter']}: {diag['value']} - {diag['issue']}")
        print()
    
    print("✅ Test complete")
