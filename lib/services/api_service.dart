import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/food_item.dart';

/// Lean HTTP service layer to keep widgets free from networking code.
class ApiService {
  const ApiService({required this.baseUrl});

  final String baseUrl;

  Future<String?> login({
    required String phone,
    required String password,
  }) async {
    // TODO: Replace with secure storage + proper error handling.
    final response = await http.post(
      Uri.parse('$baseUrl/login'),
      body: {'phone': phone, 'password': password},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return data['token'] as String?;
    }
    return null;
  }

  Future<bool> register({
    required String name,
    required String phone,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/register'),
      body: {'name': name, 'phone': phone, 'password': password},
    );
    return response.statusCode == 201;
  }

  Future<List<FoodItem>> fetchAvailableFood() async {
    final response = await http.get(Uri.parse('$baseUrl/food'));
    if (response.statusCode == 200) {
      final list = jsonDecode(response.body) as List<dynamic>;
      return list.map((item) => FoodItem.fromJson(item)).toList();
    }
    return [];
  }

  Future<bool> postFood(FoodItem item) async {
    final response = await http.post(
      Uri.parse('$baseUrl/food'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(item.toJson()),
    );
    return response.statusCode == 201;
  }

  Future<bool> requestFood({
    required String foodId,
    required String notes,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/food/$foodId/request'),
      body: {'notes': notes},
    );
    return response.statusCode == 200;
  }
}

