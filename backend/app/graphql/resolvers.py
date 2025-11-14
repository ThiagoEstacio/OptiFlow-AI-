"""
GraphQL Resolvers (PDCA #27)

Business logic for GraphQL queries and mutations.
"""

from typing import List, Optional
from datetime import datetime
import strawberry
from strawberry.types import Info

from app.graphql.types import (
    User, Site, Asset, Alarm, Gateway, DataQuality,
    AssetFilter, AlarmFilter, UpdateAssetInput, AcknowledgeAlarmInput,
    Dashboard360, ROI, OverallHealthScore, MaintenanceMetrics, OperationsMetrics,
    PredictiveMaintenanceROI, AssetType, AssetStatus, AlarmSeverity
)
from app.core.advanced_cache import cached_function


# ========================================
# Helper Functions
# ========================================

async def get_db_from_info(info: Info):
    """Extract database session from GraphQL context."""
    return info.context["db"]


async def get_current_user_from_info(info: Info) -> User:
    """Extract current user from GraphQL context."""
    return info.context["user"]


# ========================================
# Query Resolvers
# ========================================

@strawberry.type
class Query:
    """Root query type."""

    @strawberry.field
    async def current_user(self, info: Info) -> User:
        """
        Get current authenticated user.

        Example query:
        ```graphql
        query {
          currentUser {
            id
            email
            fullName
            role
          }
        }
        ```
        """
        user = await get_current_user_from_info(info)
        return User(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )

    @strawberry.field
    @cached_function(ttl=60, key_prefix="graphql_site")
    async def site(self, info: Info, id: int, period_days: int = 7) -> Site:
        """
        Get site with dashboard, ROI, assets, and alarms.

        Single query to replace 8+ REST endpoints!

        Example query:
        ```graphql
        query ExecutiveDashboard($siteId: Int!) {
          site(id: $siteId) {
            id
            name
            dashboard360 {
              overallHealthScore {
                score
                status
              }
              maintenance {
                averageHealth
                criticalAssets
              }
            }
            roi {
              totalSavings
              annualProjection
            }
            assets(limit: 10) {
              id
              name
              status
              health
            }
            alarms(limit: 5) {
              id
              message
              severity
            }
          }
        }
        ```
        """
        from app.services.executive_dashboard_optimized import ExecutiveDashboardOptimized
        from app.services.roi_calculator import ROICalculator
        from app.models.asset import Asset as AssetModel
        from app.models.alarm import Alarm as AlarmModel
        from sqlalchemy import select

        db = await get_db_from_info(info)

        # Get dashboard data (PDCA #14 optimized)
        dashboard_service = ExecutiveDashboardOptimized(db)
        dashboard_data = await dashboard_service.get_dashboard_360(id, period_days)

        # Get ROI data
        roi_service = ROICalculator(db)
        roi_data = await roi_service.calculate_roi(id, period_days)

        # Get assets
        assets_result = await db.execute(
            select(AssetModel).where(AssetModel.site_id == id).limit(10)
        )
        assets_models = assets_result.scalars().all()

        # Get alarms
        alarms_result = await db.execute(
            select(AlarmModel)
            .where(AlarmModel.asset.has(site_id=id))
            .order_by(AlarmModel.timestamp.desc())
            .limit(10)
        )
        alarms_models = alarms_result.scalars().all()

        # Build response
        overall_health = dashboard_data.get("overall_health_score", {})
        maintenance = dashboard_data.get("maintenance", {})
        operations = dashboard_data.get("operations", {})
        alarms_data = maintenance.get("alarms", {})
        predictive = roi_data.get("predictive_maintenance", {})

        return Site(
            id=str(id),
            name=f"Site {id}",
            location="Industrial Terminal",
            dashboard360=Dashboard360(
                overall_health_score=OverallHealthScore(
                    score=overall_health.get("score", 0),
                    status=overall_health.get("status", "unknown"),
                    color=overall_health.get("color", "grey")
                ),
                maintenance=MaintenanceMetrics(
                    average_health=maintenance.get("average_health_score", 0),
                    critical_assets=maintenance.get("assets_by_health", {}).get("critical", 0),
                    critical_alarms=alarms_data.get("critical", 0),
                    high_alarms=alarms_data.get("high", 0),
                    medium_alarms=alarms_data.get("medium", 0)
                ),
                operations=OperationsMetrics(
                    efficiency_score=operations.get("efficiency_score", 0),
                    berth_utilization=operations.get("berth_utilization_percent", 0)
                )
            ),
            roi=ROI(
                total_savings=roi_data.get("total_savings", 0),
                annual_projection=roi_data.get("annual_projection", 0),
                roi_percentage=roi_data.get("roi_percentage", 0),
                predictive_maintenance=PredictiveMaintenanceROI(
                    failures_prevented=predictive.get("failures_prevented", 0),
                    emergency_costs_avoided=predictive.get("emergency_costs_avoided", 0),
                    savings=predictive.get("savings", 0)
                )
            ),
            assets=[
                Asset(
                    id=str(asset.id),
                    name=asset.name,
                    type=AssetType(asset.type),
                    status=AssetStatus(asset.status),
                    health=asset.health or 0,
                    location=asset.location,
                    last_maintenance=asset.last_maintenance,
                    created_at=asset.created_at
                )
                for asset in assets_models
            ],
            alarms=[
                Alarm(
                    id=str(alarm.id),
                    message=alarm.message,
                    severity=AlarmSeverity(alarm.severity),
                    asset_id=str(alarm.asset_id) if alarm.asset_id else None,
                    acknowledged=alarm.acknowledged,
                    timestamp=alarm.timestamp
                )
                for alarm in alarms_models
            ]
        )

    @strawberry.field
    async def assets(
        self,
        info: Info,
        site_id: int,
        filter: Optional[AssetFilter] = None
    ) -> List[Asset]:
        """
        Get assets with optional filtering.

        Example query:
        ```graphql
        query {
          assets(siteId: 1, filter: { type: CONVEYOR, minHealth: 80 }) {
            id
            name
            status
            health
          }
        }
        ```
        """
        from app.models.asset import Asset as AssetModel
        from sqlalchemy import select

        db = await get_db_from_info(info)

        query = select(AssetModel).where(AssetModel.site_id == site_id)

        if filter:
            if filter.type:
                query = query.where(AssetModel.type == filter.type.value)
            if filter.status:
                query = query.where(AssetModel.status == filter.status.value)
            if filter.min_health:
                query = query.where(AssetModel.health >= filter.min_health)
            if filter.limit:
                query = query.limit(filter.limit)

        result = await db.execute(query)
        assets_models = result.scalars().all()

        return [
            Asset(
                id=str(asset.id),
                name=asset.name,
                type=AssetType(asset.type),
                status=AssetStatus(asset.status),
                health=asset.health or 0,
                location=asset.location,
                last_maintenance=asset.last_maintenance,
                created_at=asset.created_at
            )
            for asset in assets_models
        ]

    @strawberry.field
    async def alarms(
        self,
        info: Info,
        site_id: int,
        filter: Optional[AlarmFilter] = None
    ) -> List[Alarm]:
        """
        Get alarms with optional filtering.

        Example query:
        ```graphql
        query {
          alarms(siteId: 1, filter: { severity: CRITICAL, acknowledged: false }) {
            id
            message
            severity
            timestamp
          }
        }
        ```
        """
        from app.models.alarm import Alarm as AlarmModel
        from sqlalchemy import select

        db = await get_db_from_info(info)

        query = (
            select(AlarmModel)
            .join(AlarmModel.asset)
            .where(AlarmModel.asset.has(site_id=site_id))
            .order_by(AlarmModel.timestamp.desc())
        )

        if filter:
            if filter.severity:
                query = query.where(AlarmModel.severity == filter.severity.value)
            if filter.acknowledged is not None:
                query = query.where(AlarmModel.acknowledged == filter.acknowledged)
            if filter.limit:
                query = query.limit(filter.limit)

        result = await db.execute(query)
        alarms_models = result.scalars().all()

        return [
            Alarm(
                id=str(alarm.id),
                message=alarm.message,
                severity=AlarmSeverity(alarm.severity),
                asset_id=str(alarm.asset_id) if alarm.asset_id else None,
                acknowledged=alarm.acknowledged,
                timestamp=alarm.timestamp
            )
            for alarm in alarms_models
        ]

    @strawberry.field
    async def gateways(self, info: Info) -> List[Gateway]:
        """
        Get all gateways status.

        Example query:
        ```graphql
        query {
          gateways {
            id
            name
            status
            connectedTags
          }
        }
        ```
        """
        from app.models.gateway import Gateway as GatewayModel
        from sqlalchemy import select

        db = await get_db_from_info(info)

        result = await db.execute(select(GatewayModel))
        gateways_models = result.scalars().all()

        return [
            Gateway(
                id=str(gw.id),
                name=gw.name,
                status=gw.status,
                connected_tags=gw.connected_tags or 0,
                protocol=gw.protocol
            )
            for gw in gateways_models
        ]


# ========================================
# Mutation Resolvers
# ========================================

@strawberry.type
class Mutation:
    """Root mutation type."""

    @strawberry.mutation
    async def update_asset(
        self,
        info: Info,
        input: UpdateAssetInput
    ) -> Asset:
        """
        Update asset status or health.

        Example mutation:
        ```graphql
        mutation {
          updateAsset(input: { id: "123", status: MAINTENANCE, health: 75 }) {
            id
            status
            health
          }
        }
        ```
        """
        from app.models.asset import Asset as AssetModel
        from sqlalchemy import select

        db = await get_db_from_info(info)

        result = await db.execute(
            select(AssetModel).where(AssetModel.id == input.id)
        )
        asset = result.scalar_one_or_none()

        if not asset:
            raise Exception(f"Asset {input.id} not found")

        if input.status:
            asset.status = input.status.value
        if input.health is not None:
            asset.health = input.health

        await db.commit()
        await db.refresh(asset)

        return Asset(
            id=str(asset.id),
            name=asset.name,
            type=AssetType(asset.type),
            status=AssetStatus(asset.status),
            health=asset.health or 0,
            location=asset.location,
            last_maintenance=asset.last_maintenance,
            created_at=asset.created_at
        )

    @strawberry.mutation
    async def acknowledge_alarm(
        self,
        info: Info,
        input: AcknowledgeAlarmInput
    ) -> Alarm:
        """
        Acknowledge an alarm.

        Example mutation:
        ```graphql
        mutation {
          acknowledgeAlarm(input: { id: "456", userId: "789" }) {
            id
            acknowledged
          }
        }
        ```
        """
        from app.models.alarm import Alarm as AlarmModel
        from sqlalchemy import select

        db = await get_db_from_info(info)

        result = await db.execute(
            select(AlarmModel).where(AlarmModel.id == input.id)
        )
        alarm = result.scalar_one_or_none()

        if not alarm:
            raise Exception(f"Alarm {input.id} not found")

        alarm.acknowledged = True
        alarm.acknowledged_by = input.user_id
        alarm.acknowledged_at = datetime.utcnow()

        await db.commit()
        await db.refresh(alarm)

        return Alarm(
            id=str(alarm.id),
            message=alarm.message,
            severity=AlarmSeverity(alarm.severity),
            asset_id=str(alarm.asset_id) if alarm.asset_id else None,
            acknowledged=alarm.acknowledged,
            timestamp=alarm.timestamp
        )
