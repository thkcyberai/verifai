import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { VerificationResult } from '../services/api';
import { VERDICT_COLORS } from '../config/constants';

export default function ResultScreen({ route, navigation }: any) {
  const { result }: { result: VerificationResult } = route.params;

  const getVerdictColor = () => VERDICT_COLORS[result.verdict] || '#6b7280';
  
  const getConfidenceLabel = () => {
    if (result.confidence >= 0.8) return 'High Confidence';
    if (result.confidence >= 0.5) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const openURL = (url: string) => {
    Linking.openURL(url).catch(() => {
      console.error('Failed to open URL:', url);
    });
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={[styles.header, { backgroundColor: getVerdictColor() }]}>
          <Text style={styles.verdictText}>{result.verdict}</Text>
          <Text style={styles.confidenceText}>
            {getConfidenceLabel()} ({Math.round(result.confidence * 100)}%)
          </Text>
        </View>

        {/* Claim */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Claim</Text>
          <Text style={styles.claimText}>{result.claim}</Text>
        </View>

        {/* Reasoning */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Analysis</Text>
          <Text style={styles.reasoningText}>{result.reasoning}</Text>
        </View>

        {/* Evidence */}
        {result.evidence && result.evidence.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Evidence ({result.evidence.length})</Text>
            {result.evidence.map((evidence, index) => (
              <View key={index} style={styles.evidenceCard}>
                <Text style={styles.evidenceTitle}>{evidence.title}</Text>
                <Text style={styles.evidenceSnippet}>{evidence.snippet}</Text>
                <TouchableOpacity onPress={() => openURL(evidence.url)}>
                  <Text style={styles.evidenceLink}>View Source →</Text>
                </TouchableOpacity>
                <Text style={styles.relevanceScore}>
                  Relevance: {Math.round(evidence.relevance_score * 100)}%
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Sources */}
        {result.sources && result.sources.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Sources ({result.sources.length})</Text>
            {result.sources.map((source, index) => (
              <TouchableOpacity
                key={index}
                style={styles.sourceCard}
                onPress={() => openURL(source.url)}
              >
                <Text style={styles.sourceTitle}>{source.title}</Text>
                <Text style={styles.sourceURL}>{source.url}</Text>
                <Text style={styles.credibilityScore}>
                  Credibility: {Math.round(source.credibility * 100)}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Media Analysis */}
        {result.media_analysis && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Media Analysis</Text>
            <View style={styles.mediaCard}>
              <Text style={styles.mediaStatus}>
                {result.media_analysis.is_manipulated ? '⚠️ Manipulated' : '✓ Authentic'}
              </Text>
              <Text style={styles.mediaConfidence}>
                Confidence: {Math.round(result.media_analysis.confidence * 100)}%
              </Text>
              {result.media_analysis.findings.map((finding, index) => (
                <Text key={index} style={styles.mediaFinding}>• {finding}</Text>
              ))}
            </View>
          </View>
        )}

        {/* Timestamp */}
        <View style={styles.footer}>
          <Text style={styles.timestamp}>
            Verified: {new Date(result.created_at).toLocaleString()}
          </Text>
        </View>
      </ScrollView>

      {/* Bottom Button */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.newVerificationButton}
          onPress={() => navigation.navigate('Input')}
        >
          <Text style={styles.newVerificationButtonText}>Verify Another Claim</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scrollContent: { paddingBottom: 80 },
  header: { padding: 24, paddingTop: 60, alignItems: 'center' },
  verdictText: { fontSize: 32, fontWeight: 'bold', color: '#fff', marginBottom: 8 },
  confidenceText: { fontSize: 16, color: '#fff', opacity: 0.9 },
  section: { backgroundColor: '#fff', padding: 20, marginTop: 12 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#1f2937', marginBottom: 12 },
  claimText: { fontSize: 16, color: '#374151', lineHeight: 24 },
  reasoningText: { fontSize: 15, color: '#4b5563', lineHeight: 22 },
  evidenceCard: { backgroundColor: '#f9fafb', padding: 16, borderRadius: 8, marginBottom: 12, borderLeftWidth: 3, borderLeftColor: '#3b82f6' },
  evidenceTitle: { fontSize: 15, fontWeight: '600', color: '#1f2937', marginBottom: 8 },
  evidenceSnippet: { fontSize: 14, color: '#6b7280', lineHeight: 20, marginBottom: 8 },
  evidenceLink: { fontSize: 14, color: '#2563eb', fontWeight: '500' },
  relevanceScore: { fontSize: 12, color: '#9ca3af', marginTop: 8 },
  sourceCard: { backgroundColor: '#f9fafb', padding: 16, borderRadius: 8, marginBottom: 12 },
  sourceTitle: { fontSize: 15, fontWeight: '600', color: '#1f2937', marginBottom: 4 },
  sourceURL: { fontSize: 13, color: '#2563eb', marginBottom: 8 },
  credibilityScore: { fontSize: 12, color: '#9ca3af' },
  mediaCard: { backgroundColor: '#fef3c7', padding: 16, borderRadius: 8 },
  mediaStatus: { fontSize: 16, fontWeight: 'bold', color: '#92400e', marginBottom: 8 },
  mediaConfidence: { fontSize: 14, color: '#78350f', marginBottom: 12 },
  mediaFinding: { fontSize: 14, color: '#78350f', lineHeight: 20, marginBottom: 4 },
  footer: { padding: 20, alignItems: 'center' },
  timestamp: { fontSize: 12, color: '#9ca3af' },
  bottomBar: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: '#fff', padding: 16, borderTopWidth: 1, borderTopColor: '#e5e7eb' },
  newVerificationButton: { backgroundColor: '#2563eb', borderRadius: 12, padding: 16, alignItems: 'center' },
  newVerificationButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
