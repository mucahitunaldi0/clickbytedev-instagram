import 'package:flutter/material.dart';

Widget liste(List<String> urunler) {
  return ListView.builder(
    itemCount: urunler.length,
    itemBuilder: (context, i) {
      return ListTile(title: Text(urunler[i]));
    },
  );
}
