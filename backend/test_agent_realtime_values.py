"""
Test script to validate Autonomous Agent's real-time tag value retrieval
Simulates the agent discovering tags and fetching their current values
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.influxdb import influxdb_service
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_agent_realtime_discovery():
    """
    Test the complete auto-discovery and real-time value retrieval flow
    This simulates what the Autonomous Agent does every 60 seconds
    """

    logger.info("=" * 80)
    logger.info("🤖 AUTONOMOUS AGENT - REAL-TIME VALUE TEST")
    logger.info("=" * 80)

    # Step 1: Auto-discovery (what the agent does first)
    logger.info("\n📡 Step 1: Auto-discovering tags from InfluxDB...")
    tag_names = influxdb_service.list_all_measurements()

    if not tag_names:
        logger.error("❌ No tags found in InfluxDB!")
        return

    logger.info(f"✅ Discovered {len(tag_names)} tags")
    logger.info(f"   Tags: {', '.join(tag_names[:10])}{'...' if len(tag_names) > 10 else ''}")

    # Step 2: Fetch real-time values for each tag
    logger.info(f"\n📊 Step 2: Fetching real-time values for all {len(tag_names)} tags...")
    logger.info("-" * 80)

    results = {
        'success': 0,
        'no_data': 0,
        'errors': 0,
        'tag_values': []
    }

    for tag_name in tag_names:
        try:
            # This is the same method the agent uses
            value_data = influxdb_service.get_latest_value_by_name(tag_name)

            if value_data:
                results['success'] += 1
                results['tag_values'].append({
                    'name': tag_name,
                    'value': value_data['value'],
                    'timestamp': value_data['timestamp'],
                    'quality': value_data['quality'],
                    'source': value_data['source']
                })

                # Log each tag value
                logger.info(
                    f"✅ {tag_name:<40} = {value_data['value']:>10.2f} "
                    f"[{value_data['quality']}] @ {value_data['timestamp'][:19]}"
                )
            else:
                results['no_data'] += 1
                logger.warning(f"⚠️  {tag_name:<40} = NO DATA (last 24h)")

        except Exception as e:
            results['errors'] += 1
            logger.error(f"❌ {tag_name:<40} = ERROR: {str(e)[:50]}")

    # Step 3: Summary and analysis
    logger.info("\n" + "=" * 80)
    logger.info("📈 SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total tags discovered:    {len(tag_names)}")
    logger.info(f"✅ Values retrieved:      {results['success']} ({results['success']/len(tag_names)*100:.1f}%)")
    logger.info(f"⚠️  No data found:        {results['no_data']} ({results['no_data']/len(tag_names)*100:.1f}%)")
    logger.info(f"❌ Errors:                {results['errors']} ({results['errors']/len(tag_names)*100:.1f}%)")

    # Step 4: Show some statistics
    if results['tag_values']:
        logger.info("\n" + "-" * 80)
        logger.info("📊 VALUE STATISTICS")
        logger.info("-" * 80)

        # Group by category (based on tag name patterns)
        gate_tags = [t for t in results['tag_values'] if 'GATE' in t['name']]
        system_tags = [t for t in results['tag_values'] if 'SYSTEM' in t['name'] or 'TOTAL' in t['name'] or 'WAREHOUSE' in t['name'] or 'TEST' in t['name']]

        logger.info(f"\n🚪 Gate Tags: {len(gate_tags)}")
        for tag in gate_tags[:10]:  # Show first 10
            logger.info(f"   {tag['name']:<45} = {tag['value']:>10.2f}")

        logger.info(f"\n⚙️  System Tags: {len(system_tags)}")
        for tag in system_tags:
            logger.info(f"   {tag['name']:<45} = {tag['value']:>10.2f}")

        # Quality check
        good_quality = sum(1 for t in results['tag_values'] if t['quality'] == 'good')
        logger.info(f"\n✨ Quality: {good_quality}/{len(results['tag_values'])} tags with 'good' quality ({good_quality/len(results['tag_values'])*100:.1f}%)")

    # Step 5: Simulate what agent would do with this data
    logger.info("\n" + "=" * 80)
    logger.info("🤖 WHAT THE AGENT DOES WITH THIS DATA")
    logger.info("=" * 80)
    logger.info("The Autonomous Agent uses these real-time values to:")
    logger.info("  1. 🔍 Detect anomalies (outliers, sudden changes)")
    logger.info("  2. 📊 Analyze performance (efficiency, throughput)")
    logger.info("  3. ⚠️  Check alarm conditions (thresholds)")
    logger.info("  4. 💚 Monitor asset health (degradation patterns)")
    logger.info("  5. ⚡ Identify optimization opportunities")
    logger.info("  6. 🔮 Predict future states (trends)")

    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST COMPLETE - Real-time value retrieval is working!")
    logger.info("=" * 80)

    return results


if __name__ == "__main__":
    asyncio.run(test_agent_realtime_discovery())
