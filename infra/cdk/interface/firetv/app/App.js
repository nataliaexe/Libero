/**
 * Libero - Fire TV App
 * Interface do idoso: reminiscência, conversa, emergência.
 */

import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, Pressable, ScrollView, Alert } from 'react-native';
import { StatusBar } from 'expo-status-bar';

export default function App() {
  const [tela, setTela] = useState('inicio');
  const [idoso] = useState({ nome: 'Dona Maria' });
  const [hora, setHora] = useState(new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));
  const [memorias] = useState([]);

  // Atualizar hora
  useEffect(() => {
    const timer = setInterval(() => {
      setHora(new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  // Tela inicial
  const TelaInicial = () => (
    <View style={styles.container}>
      <StatusBar style="light" />
      <Text style={styles.saudacao}>Bom dia, {idoso.nome}</Text>
      <Text style={styles.hora}>{hora}</Text>
      <View style={styles.botoes}>
        <BotaoGrande
          titulo="Minhas Memórias"
          onPress={() => setTela('memorias')}
        />
        <BotaoGrande
          titulo="Conversar"
          onPress={() => setTela('conversa')}
        />
        <BotaoGrande
          titulo="Chamar Ajuda"
          onPress={() => setTela('emergencia')}
          cor="#c0392b"
        />
      </View>
    </View>
  );

  // Tela de memórias
  const TelaMemorias = () => (
    <View style={styles.container}>
      <Text style={styles.titulo}>Minhas Memórias</Text>
      <ScrollView style={styles.lista}>
        {memorias.length === 0 ? (
          <Text style={styles.vazio}>Nenhuma memória ainda. Conte uma história!</Text>
        ) : (
          memorias.map((m, i) => (
            <View key={i} style={styles.memoria}>
              <Text style={styles.memoriaTitulo}>{m.titulo}</Text>
              <Text style={styles.memoriaResumo}>{m.resumo}</Text>
            </View>
          ))
        )}
      </ScrollView>
      <BotaoGrande titulo="Voltar" onPress={() => setTela('inicio')} />
    </View>
  );

  // Tela de conversa
  const TelaConversa = () => (
    <View style={styles.container}>
      <Text style={styles.titulo}>Conversar</Text>
      <Text style={styles.instrucao}>Protótipo: interação de voz ainda não conectada</Text>
      <View style={styles.avatar}>
        <Text style={styles.avatarTexto}>L</Text>
      </View>
      <BotaoGrande titulo="Voltar" onPress={() => setTela('inicio')} />
    </View>
  );

  // Tela de emergência
  const TelaEmergencia = () => (
    <View style={[styles.container, styles.emergencia]}>
      <Text style={styles.tituloEmergencia}>Chamar Ajuda</Text>
      <Text style={styles.instrucaoEmergencia}>
        Demonstração experimental. Nenhuma mensagem ou chamada será enviada.
      </Text>
      <Pressable
        style={styles.botaoEmergencia}
        onPress={chamarEmergencia}
      >
        <Text style={styles.botaoEmergenciaTexto}>VER DEMONSTRAÇÃO</Text>
      </Pressable>
      <BotaoGrande titulo="Cancelar" onPress={() => setTela('inicio')} />
    </View>
  );

  const chamarEmergencia = () => Alert.alert(
    'Demonstração',
    'Nenhuma notificação foi enviada. O Libero não contata serviços de emergência.'
  );

  // Roteamento
  if (tela === 'memorias') return <TelaMemorias />;
  if (tela === 'conversa') return <TelaConversa />;
  if (tela === 'emergencia') return <TelaEmergencia />;
  return <TelaInicial />;
}

// Botão grande para TV
function BotaoGrande({ titulo, onPress, cor = '#3498db' }) {
  return (
    <Pressable style={[styles.botao, { backgroundColor: cor }]} onPress={onPress}>
      <Text style={styles.botaoTexto}>{titulo}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40
  },
  saudacao: {
    fontSize: 48,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 20
  },
  hora: {
    fontSize: 96,
    color: '#e94560',
    fontWeight: 'bold',
    marginBottom: 60
  },
  botoes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 20
  },
  botao: {
    paddingHorizontal: 40,
    paddingVertical: 30,
    borderRadius: 16,
    minWidth: 250,
    alignItems: 'center'
  },
  botaoTexto: {
    fontSize: 28,
    color: '#ffffff',
    fontWeight: '600'
  },
  titulo: {
    fontSize: 42,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 30
  },
  lista: {
    width: '100%',
    maxHeight: 400
  },
  memoria: {
    backgroundColor: '#16213e',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15
  },
  memoriaTitulo: {
    fontSize: 24,
    color: '#e94560',
    fontWeight: 'bold'
  },
  memoriaResumo: {
    fontSize: 18,
    color: '#ffffff',
    marginTop: 8
  },
  vazio: {
    fontSize: 20,
    color: '#888',
    textAlign: 'center'
  },
  instrucao: {
    fontSize: 24,
    color: '#ffffff',
    marginBottom: 30
  },
  avatar: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: '#e94560',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 40
  },
  avatarTexto: {
    fontSize: 120,
    color: '#ffffff',
    fontWeight: 'bold'
  },
  emergencia: {
    backgroundColor: '#2c0e0e'
  },
  tituloEmergencia: {
    fontSize: 56,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 20
  },
  instrucaoEmergencia: {
    fontSize: 24,
    color: '#ffcccc',
    marginBottom: 40,
    textAlign: 'center'
  },
  botaoEmergencia: {
    backgroundColor: '#c0392b',
    paddingHorizontal: 80,
    paddingVertical: 40,
    borderRadius: 20,
    marginBottom: 40
  },
  botaoEmergenciaTexto: {
    fontSize: 32,
    color: '#ffffff',
    fontWeight: 'bold'
  }
});
