/// Serializable data model representing a posted meal entry.
class FoodItem {
  FoodItem({
    required this.id,
    required this.title,
    required this.pickupLat,
    required this.pickupLng,
    required this.pickupAddress,
    required this.quantity,
    required this.availableUntil,
    required this.items,
  });

  final String id;
  final String title;
  final double pickupLat;
  final double pickupLng;
  final String pickupAddress;
  final String quantity;
  final DateTime availableUntil;
  final List<String> items;

  factory FoodItem.fromJson(Map<String, dynamic> json) => FoodItem(
        id: json['id'] as String,
        title: json['title'] as String,
        pickupLat: (json['pickup_lat'] as num).toDouble(),
        pickupLng: (json['pickup_lng'] as num).toDouble(),
        pickupAddress: json['pickup_address'] as String,
        quantity: json['quantity'] as String,
        availableUntil: DateTime.parse(json['available_until'] as String),
        items: List<String>.from(json['items'] ?? const []),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'pickup_lat': pickupLat,
        'pickup_lng': pickupLng,
        'pickup_address': pickupAddress,
        'quantity': quantity,
        'available_until': availableUntil.toIso8601String(),
        'items': items,
      };
}

