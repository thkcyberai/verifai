import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { apiService } from '../services/api';

export default function InputScreen({ navigation }: any) {
  const [claim, setClaim] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!claim.trim()) {
      Alert.alert('Error', 'Please enter a claim');
      return;
    }

    setLoading(true);

    try {
      const result = await apiService.verify({
        claim: claim.trim(),
        language: 'en-US',
      });

      navigation.navigate('Result', { result });
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>VerifAI</Text>
          <Text style={styles.subtitle}>Is this true?</Text>
        </View>

        <View style={styles.content}>
          <Text style={styles.label}>Enter a claim to verify:</Text>
          <TextInput
            style={styles.textInput}
            placeholder="E.g., The Earth is flat"
            placeholderTextColor="#999"
            value={claim}
            onChangeText={setClaim}
            multiline
            numberOfLines={4}
            maxLength={2000}
            editable={!loading}
          />

          <Text style={styles.charCount}>{claim.length} / 2000</Text>

          <TouchableOpacity
            style={[styles.verifyButton, !claim.trim() || loading ? styles.verifyButtonDisabled : {}]}
            onPress={handleVerify}
            disabled={!claim.trim() || loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.verifyButtonText}>Verify Claim</Text>
            )}
          </TouchableOpacity>

          {claim && !loading && (
            <TouchableOpacity style={styles.clearButton} onPress={() => setClaim('')}>
              <Text style={styles.clearButtonText}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Powered by AI • Web Search • Media Forensics</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scrollContent: { flexGrow: 1 },
  header: { backgroundColor: '#2563eb', padding: 24, paddingTop: 60, alignItems: 'center' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#fff', marginBottom: 8 },
  subtitle: { fontSize: 18, color: '#dbeafe' },
  content: { flex: 1, padding: 20 },
  label: { fontSize: 16, fontWeight: '600', color: '#374151', marginBottom: 8 },
  textInput: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    minHeight: 120,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  charCount: { fontSize: 12, color: '#9ca3af', textAlign: 'right', marginTop: 4, marginBottom: 16 },
  verifyButton: { backgroundColor: '#2563eb', borderRadius: 12, padding: 18, alignItems: 'center', marginTop: 32 },
  verifyButtonDisabled: { backgroundColor: '#9ca3af' },
  verifyButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  clearButton: { padding: 12, alignItems: 'center', marginTop: 12 },
  clearButtonText: { color: '#6b7280', fontSize: 16 },
  footer: { padding: 20, alignItems: 'center' },
  footerText: { fontSize: 12, color: '#9ca3af' },
});
