/**
 * Libero - Mobile App
 * Interface da família: dashboard, alertas, memórias.
 */

import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, Pressable, RefreshControl } from 'react-native';
import { StatusBar } from 'expo-status-bar';

const API_URL = process.env.LIBERO_API_URL || 'http://localhost:8080';

export default function App() {
  const [aba, setAba] = useState('dashboard');
  const [refreshing, setRefreshing] = useState(false);
  const [estado, setEstado] = useState({
    nome: 'Dona Maria',
    humor: 'calmo',
    sono: '7h',
    remedios: 'ok',
    episodios: 1,
    memorias: 47,
    ultimaAtualizacao: new Date().toLocaleTimeString('pt-BR')
  });
  const [alertas, setAlertas] = useState([]);
  const [memorias, setMemorias] = useState([]);

  const carregarDados = async () => {
    setRefreshing(true);
    try {
      const resp = await fetch(`${API_URL}/health`);
      const dados = await resp.json();
      console.log('Health:', dados);
    } catch (e) {
      console.error('Erro:', e);
    }
    setRefreshing(false);
  };

  useEffect(() => {
    carregarDados();
  }, []);

  // Dashboard
  const Dashboard = () => (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={carregarDados} />
      }
    >
      <StatusBar style="dark" />
      <Text style={styles.titulo}>Dashboard</Text>
      <Text style={styles.subtitulo}>{estado.nome}</Text>
      <Text style={styles.atualizacao}>Atualizado às {estado.ultimaAtualizacao}</Text>

      <View style={styles.cards}>
        <Card titulo="Humor" valor={estado.humor} cor="#3498db" />
        <Card titulo="Sono" valor={estado.sono} cor="#9b59b6" />
        <Card titulo="Remédios" valor={estado.remedios} cor="#27ae60" />
        <Card titulo="Episódios" valor={estado.episodios} cor="#e67e22" />
        <Card titulo="Memórias" valor={estado.memorias} cor="#e94560" />
      </View>

      <Text style={styles.secao}>Últimos Alertas</Text>
      {alertas.length === 0 ? (
        <Text style={styles.vazio}>Nenhum alerta recente. Tudo tranquilo.</Text>
      ) : (
        alertas.map((a, i) => (
          <View key={i} style={styles.alerta}>
            <Text style={styles.alertaTexto}>{a.mensagem}</Text>
            <Text style={styles.alertaHora}>{a.hora}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );

  // Memórias
  const Memorias = () => (
    <ScrollView style={styles.container}>
      <Text style={styles.titulo}>Memórias</Text>
      <Text style={styles.subtitulo}>Histórias contadas por {estado.nome}</Text>
      {memorias.length === 0 ? (
        <Text style={styles.vazio}>Nenhuma memória gravada ainda.</Text>
      ) : (
        memorias.map((m, i) => (
          <View key={i} style={styles.memoria}>
            <Text style={styles.memoriaTitulo}>{m.titulo}</Text>
            <Text style={styles.memoriaResumo}>{m.resumo}</Text>
            <Text style={styles.memoriaData}>{m.data}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );

  // Configurações
  const Configuracoes = () => (
    <ScrollView style={styles.container}>
      <Text style={styles.titulo}>Configurações</Text>
      <Item titulo="Privacidade" valor="Ativada" />
      <Item titulo="Câmera em emergências" valor="Sim" />
      <Item titulo="Notificações" valor="Todas" />
      <Item titulo="Zonas de exclusão" valor="Banheiro, Quarto" />
      <Item titulo="Compliance" valor="LGPD, GDPR, HIPAA" />
    </ScrollView>
  );

  // Navegação
  return (
    <View style={styles.app}>
      <View style={styles.conteudo}>
        {aba === 'dashboard' && <Dashboard />}
        {aba === 'memorias' && <Memorias />}
        {aba === 'config' && <Configuracoes />}
      </View>
      <View style={styles.tabs}>
        <Tab ativo={aba === 'dashboard'} titulo="Início" onPress={() => setAba('dashboard')} />
        <Tab ativo={aba === 'memorias'} titulo="Memórias" onPress={() => setAba('memorias')} />
        <Tab ativo={aba === 'config'} titulo="Ajustes" onPress={() => setAba('config')} />
      </View>
    </View>
  );
}

function Card({ titulo, valor, cor }) {
  return (
    <View style={[styles.card, { borderLeftColor: cor }]}>
      <Text style={styles.cardTitulo}>{titulo}</Text>
      <Text style={[styles.cardValor, { color: cor }]}>{valor}</Text>
    </View>
  );
}

function Item({ titulo, valor }) {
  return (
    <View style={styles.item}>
      <Text style={styles.itemTitulo}>{titulo}</Text>
      <Text style={styles.itemValor}>{valor}</Text>
    </View>
  );
}

function Tab({ ativo, titulo, onPress }) {
  return (
    <Pressable style={[styles.tab, ativo && styles.tabAtivo]} onPress={onPress}>
      <Text style={[styles.tabTexto, ativo && styles.tabTextoAtivo]}>{titulo}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  app: { flex: 1, backgroundColor: '#f5f5f5' },
  conteudo: { flex: 1 },
  container: { flex: 1, padding: 20 },
  titulo: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a2e',
    marginBottom: 8
  },
  subtitulo: {
    fontSize: 18,
    color: '#666',
    marginBottom: 8
  },
  atualizacao: {
    fontSize: 12,
    color: '#999',
    marginBottom: 20
  },
  cards: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 30
  },
  card: {
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    minWidth: 100,
    flex: 1
  },
  cardTitulo: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4
  },
  cardValor: {
    fontSize: 24,
    fontWeight: 'bold'
  },
  secao: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1a1a2e',
    marginBottom: 16
  },
  vazio: {
    fontSize: 16,
    color: '#999',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20
  },
  alerta: {
    backgroundColor: '#fff3cd',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8
  },
  alertaTexto: {
    fontSize: 16,
    color: '#856404'
  },
  alertaHora: {
    fontSize: 12,
    color: '#856404',
    marginTop: 4
  },
  memoria: {
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12
  },
  memoriaTitulo: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#e94560',
    marginBottom: 8
  },
  memoriaResumo: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8
  },
  memoriaData: {
    fontSize: 12,
    color: '#999'
  },
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8
  },
  itemTitulo: {
    fontSize: 16,
    color: '#333'
  },
  itemValor: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600'
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#eee'
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center'
  },
  tabAtivo: {
    borderTopWidth: 3,
    borderTopColor: '#e94560'
  },
  tabTexto: {
    fontSize: 14,
    color: '#999'
  },
  tabTextoAtivo: {
    color: '#e94560',
    fontWeight: 'bold'
  }
});
