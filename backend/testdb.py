import psycopg2
try:
      conn = psycopg2.connect(
          host='10.9.0.99',
          database='postgres',  # Base par défaut
          user='postgres',
          password='aristobot'
      )
      print('Connexion OK à postgres')
      conn.close()
except Exception as e:
      print(f'Erreur postgres: {e}')

try:
      conn = psycopg2.connect(
          host='10.9.0.99',
          database='aristobot3',  # Ta base
          user='postgres',
          password='aristobot'
      )
      print('Connexion OK à aristobot3')
      conn.close()
except Exception as e:
      print(f'Erreur aristobot3: {e}')
  
