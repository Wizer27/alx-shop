import 'dart:convert';
import  'dart:io';
import 'package:shelf/shelf.dart';
import 'package:shelf_router/shelf_router.dart';


final app = Router();



Future<Map<String, dynamic>> readJsonFile(String filePath) async {
  try {
    final file = File(filePath);
    final contents = await file.readAsString();
    return jsonDecode(contents) as Map<String, dynamic>;
  } catch (e) {
    print('Error reading file: $e');
    return {};
  }
}
Future<void> write_json_file(String file_path,Map<String,dynamic> data) async {

}

Response register(Request request) async {
    try{
        final body = request.readAsString();
        final data = jsonDecode(body);
        var final username = data['username'];
        var final psw = data['psw'];
        Future<Map<String, dynamic>> = readJson()
    }catch(e){
        print('Exception $e');
    }

}

