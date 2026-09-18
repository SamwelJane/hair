import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    WAREHOUSE = "WAREHOUSE"
    KENYA_OPS = "KENYA_OPS"


class HairCategory(str, enum.Enum):
    BULK_HAIR = "BULK_HAIR"
    EXTENSION = "EXTENSION"
    WIG = "WIG"
    CLOSURE = "CLOSURE"
    FRONTAL = "FRONTAL"
    MACHINE_WEFT = "MACHINE_WEFT"


class DrawnType(str, enum.Enum):
    SINGLE_DRAWN = "SINGLE_DRAWN"
    DOUBLE_DRAWN = "DOUBLE_DRAWN"
    SUPER_DOUBLE_DRAWN = "SUPER_DOUBLE_DRAWN"


class TextureCategory(str, enum.Enum):
    STRAIGHT = "STRAIGHT"
    WAVY = "WAVY"
    CURLY = "CURLY"


class AttachmentType(str, enum.Enum):
    SILK = "SILK"
    TAPE = "TAPE"
    CLIP_IN = "CLIP_IN"
    PONYTAIL = "PONYTAIL"
    NANO_RING = "NANO_RING"


class TipType(str, enum.Enum):
    I_TIP = "I_TIP"
    U_TIP = "U_TIP"
    FLAT_TIP = "FLAT_TIP"
    V_TIP = "V_TIP"


class WigConstruction(str, enum.Enum):
    LACE_FRONT = "LACE_FRONT"
    FULL_LACE = "FULL_LACE"
    CLOSURE_WIG = "CLOSURE_WIG"
    U_PART = "U_PART"
    GLUELESS = "GLUELESS"


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    SENT_TO_SUPPLIER = "SENT_TO_SUPPLIER"
    SUPPLIER_PROCESSING = "SUPPLIER_PROCESSING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    RECEIVED_AT_OFFICE = "RECEIVED_AT_OFFICE"
    SHIPPED_INTERNATIONALLY = "SHIPPED_INTERNATIONALLY"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ReturnStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"


class PaymentProviderType(str, enum.Enum):
    MPESA = "MPESA"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(str, enum.Enum):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SupplierOrderStatus(str, enum.Enum):
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PRODUCTION = "IN_PRODUCTION"
    READY = "READY"
    DECLINED = "DECLINED"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class DiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class WarehouseType(str, enum.Enum):
    VN = "VN"
    KE = "KE"


class ExternalShipmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class PackageStatus(str, enum.Enum):
    EXPECTED = "EXPECTED"
    RECEIVED = "RECEIVED"
    READY_FOR_CONSOLIDATION = "READY_FOR_CONSOLIDATION"
    CONSOLIDATED = "CONSOLIDATED"
    IN_TRANSIT = "IN_TRANSIT"
    AT_CUSTOMS_KENYA = "AT_CUSTOMS_KENYA"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    EXCEPTION = "EXCEPTION"


class PackageQCStatus(str, enum.Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class PackageCondition(str, enum.Enum):
    GOOD = "GOOD"
    DAMAGED = "DAMAGED"


class ConsolidationStatus(str, enum.Enum):
    OPEN = "OPEN"
    READY_FOR_EXPORT = "READY_FOR_EXPORT"
    DEPARTED = "DEPARTED"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED = "ARRIVED"
    CLOSED = "CLOSED"


class CustomsStatus(str, enum.Enum):
    PREPARING = "PREPARING"
    DECLARED = "DECLARED"
    QUERY_RAISED = "QUERY_RAISED"
    CLEARED = "CLEARED"


class OpsExceptionType(str, enum.Enum):
    SUPPLIER_DELAYED = "SUPPLIER_DELAYED"
    SUPPLIER_FAILED_TO_DISPATCH = "SUPPLIER_FAILED_TO_DISPATCH"
    PACKAGE_MISSING = "PACKAGE_MISSING"
    PACKAGE_DAMAGED = "PACKAGE_DAMAGED"
    WRONG_PACKAGE = "WRONG_PACKAGE"
    WEIGHT_MISMATCH = "WEIGHT_MISMATCH"
    PRODUCT_MISMATCH = "PRODUCT_MISMATCH"
    QC_FAILURE = "QC_FAILURE"
    SHIPMENT_DELAYED = "SHIPMENT_DELAYED"
    CUSTOMS_QUERY = "CUSTOMS_QUERY"
    CUSTOMS_HOLD = "CUSTOMS_HOLD"
    CUSTOMS_ISSUE = "CUSTOMS_ISSUE"
    DELIVERY_FAILED = "DELIVERY_FAILED"
    CUSTOMER_UNAVAILABLE = "CUSTOMER_UNAVAILABLE"
    WRONG_ADDRESS = "WRONG_ADDRESS"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    RETURNED_SHIPMENT = "RETURNED_SHIPMENT"


class OpsExceptionSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OpsExceptionStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class HomepagePlacementSection(str, enum.Enum):
    FEATURED = "FEATURED"
    DEAL = "DEAL"
