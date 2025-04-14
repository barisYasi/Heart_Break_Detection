import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import serial
import time

# Geliştiiridğimiz ardinho projesinden verilerimizi koda çekme işlemini yapalım
def kalp_hizini_al():
    try:
        ser = serial.Serial('/dev/tty.usbmodemFX2348N1', 9600, timeout=2)  # Serial portu anlık veri alıcak şekilde güncelleyelim
        time.sleep(2)  # Bağlantının kurulmasını bekle
        nabiz = None
        sayac = 0

        print("Arduino'dan nabız verisi bekleniyor...")

        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if line and line.isdigit():  
                sayac += 1
                print(f"{sayac}. Veri: {line} BPM")  # Hangi veriyi okuduğumuzu görmek için sayaç değerini yazdırıyoruz
                
                if sayac == 15:  # İlk kullanımda bazen doğru değer vermediğği için en sağlıklı olduğunu düşündüğümüz 15. değeri alacağız
                    nabiz = int(line)
                    print(f"✅ **Kullanılan Nabız Verisi:** {nabiz} BPM")
                    break  
        ser.close()  # BPM değerini aldıktan sonra serial portu kapatıyoruz
        return nabiz
    except Exception as e:
        print(f"Arduino'da  bağlantı hatası mevcut: {e}")
        return None

# Verisetimizi yükleyelim
data_yolu= 'Kalp Krizi/Dataset_back_up/cardio_train.csv'
df = pd.read_csv(data_yolu, delimiter=';')

# Veristemizdeki yaş sutünü gün formatında olduğu için yıla çevirmeliyiz onu 
df['age_years'] = df['age'] // 365

# BMI(Kilo/boy) hesaplaması yapalım
df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)

# Girilen yaşa göre kullanıcın yaş verisinin hangi yaş grubuna ait olduğunu sınıflandırdık
df['age_category'] = pd.cut(df['age_years'], 
    bins=[0, 30, 40, 50, 60, 100], 
    labels=['Young', 'Young Adult', 'Middle Age', 'Senior', 'Elderly'])

# Kategorik değişkenleri one-hot encoding ile dönüştürme
df = pd.get_dummies(df, columns=['gender', 'cholesterol', 'age_category'])

# Verisetimizde istemediğimiz birkaç veri başlkığı var onları drop fonskiyonu ile kaldıroyoruz
df = df.drop(columns=['gluc', 'id', 'age'])

# Hedef değişkeni belirleyelim
y = df['cardio']
X = df.drop(columns=['cardio'])

# Aldığımız ve akabinde düzenlediğimiz verisetini test ve eğitim verileri olmak üzere ayıralım
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Veriyi ölçeklendirme
scaler = MinMaxScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Yapay sinir ağı modeli
model = keras.Sequential([
    keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],), kernel_regularizer=keras.regularizers.l2(0.001)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.3),
    
    keras.layers.Dense(32, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.3),
    
    keras.layers.Dense(16, activation='relu'),
    keras.layers.BatchNormalization(),
    
    keras.layers.Dense(1, activation='sigmoid')
])

# Modeli derleyelim
optimizer = keras.optimizers.Adam(learning_rate=0.001)
model.compile(
    optimizer=optimizer, 
    loss='binary_crossentropy', 
    metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
)

# Callback'ler
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.00001)

# Modelimizi eğitelim
history = model.fit(
    X_train, y_train, 
    epochs=100, 
    batch_size=64, 
    validation_split=0.2, 
    callbacks=[early_stopping, reduce_lr],
    verbose=1
)

# Modelimizin performansınız ölçelim
test_loss, test_acc, test_precision, test_recall = model.evaluate(X_test, y_test)
print(f'Test Accuracy değeri: {test_acc:.4f}')
print(f'Test Precision değeri : {test_precision:.4f}')
print(f'Test Recall değeri : {test_recall:.4f}')

# Kullanıcıdan veri alarak tahmin yapma fonksiyonu
def kalp_kriz_tahmin():
    yaş = int(input("Yaşınızı girin: "))
    cinsiyet = int(input("Cinsiyet (1: Erkek, 0: Kadın): "))
    boy = int(input("Boy (cm): "))
    kilo = int(input("Kilo (kg): "))
    büyük_tansiyon= int(input("Sistolik Tansiyon: "))
    küçük_tansiyon = int(input("Diastolik Tansiyon: "))
    kolesterol = int(input("Kolesterol (1, 2, 3): "))
    sigara = int(input("Sigara (0: Hayır, 1: Evet): "))
    alkol= int(input("Alkol (0: Hayır, 1: Evet): "))
    aktivite_derecesi = int(input("Aktivite durumunuzu değerlendirin (0: Hayır, 1: Evet): "))
    

    kalp_ritmi= kalp_hizini_al()

    #Şayet ardunho projemizden veriyi alamazsak kalp ritminin maunel olarak girilmesini sağlıyoruz
    if kalp_ritmi is None:
        kalp_ritmi = int(input("Kalp atış hızınızı manuel girin: "))
    
    input_data = pd.DataFrame({
        'age_years': [yaş],
        'height': [boy],
        'weight': [kilo],
        'ap_hi': [büyük_tansiyon],
        'ap_lo': [küçük_tansiyon],
        'smoke': [sigara],
        'alco': [alkol],
        'active': [aktivite_derecesi],
        'gender': [cinsiyet],
        'cholesterol': [kolesterol],
        'bmi': [kilo / ((boy / 100) ** 2)],
        'heart_rate': [kalp_ritmi]
    })
    
    input_data['age_category'] = pd.cut(input_data['age_years'], bins=[0, 30, 40, 50, 60, 100], labels=['Young', 'Young Adult', 'Middle Age', 'Senior', 'Elderly'])
    input_data = pd.get_dummies(input_data, columns=['gender', 'cholesterol', 'age_category'])
    
    for col in X.columns:
        if col not in input_data.columns:
            input_data[col] = 0
    
    input_data = input_data[X.columns]
    input_scaled = scaler.transform(input_data)
    prediction = model.predict(input_scaled)
    
    #Kalp krizi riskini ve modelin başarı oranını yazdıralım
    print(f"Kalp krizi riski: {prediction[0][0]:.2f}")
    print(f"Model Accuracy: {test_acc:.4f}")

# Modelimizi kaydedelim
model.save('kalp_hastaligi_modeli.h5')

# Ve son olarak kullanıcıdan veri alarak kolon kanseri olup olmadığını öğrenelim.
kalp_kriz_tahmin()
