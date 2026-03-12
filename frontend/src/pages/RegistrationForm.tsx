import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

// Описуємо схему валідації за допомогою Zod
const formSchema = z.object({
  username: z.string().min(3, "Ім'я має містити щонайменше 3 символи"),
  email: z.string().email("Введіть коректну email адресу"),
  password: z.string().min(8, "Пароль має містити щонайменше 8 символів"),
});

// Витягуємо TypeScript тип автоматично зі схеми
type FormData = z.infer<typeof formSchema>;

export default function RegistrationForm() {
  // Ініціалізуємо хук useForm
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema), // Підключаємо Zod до форми
    mode: "onBlur", // Валідація спрацьовуватиме, коли користувач покидає поле
  });

  // Функція обробки успішної валідації
  const onSubmit = async (data: FormData) => {
    try {

      // Тут має бути реальний запит на бекенд!!!!!!!!!!!!!!!

      await new Promise((resolve) => setTimeout(resolve, 1500));

      console.log("Дані, готові до відправки:", data);
      alert("Форма успішно відправлена!");

      // Очищаємо форму після успішної відправки
      reset();
    } catch (error) {
      console.error("Помилка відправки:", error);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white border border-gray-200 rounded-2xl shadow-sm">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Реєстрація</h2>

      {/* handleSubmit автоматично зупинить відправку, якщо є помилки валідації */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

        {/* Поле Username */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ім'я користувача
          </label>
          <input
            {...register("username")}
            type="text"
            placeholder="Введіть ім'я"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${errors.username
              ? "border-red-500 focus:ring-red-200"
              : "border-gray-300 focus:ring-blue-200 focus:border-blue-500"
              }`}
          />
          {/* Виведення повідомлення про помилку */}
          {errors.username && (
            <p className="mt-1 text-sm text-red-500">{errors.username.message}</p>
          )}
        </div>

        {/* Поле Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            {...register("email")}
            type="email"
            placeholder="example@mail.com"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${errors.email
              ? "border-red-500 focus:ring-red-200"
              : "border-gray-300 focus:ring-blue-200 focus:border-blue-500"
              }`}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-500">{errors.email.message}</p>
          )}
        </div>

        {/* Поле Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Пароль
          </label>
          <input
            {...register("password")}
            type="password"
            placeholder="••••••••"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${errors.password
              ? "border-red-500 focus:ring-red-200"
              : "border-gray-300 focus:ring-blue-200 focus:border-blue-500"
              }`}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-500">{errors.password.message}</p>
          )}
        </div>

        {/* Кнопка Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed flex justify-center items-center"
        >
          {isSubmitting ? (
            <span className="animate-pulse">Відправка...</span>
          ) : (
            "Зареєструватися"
          )}
        </button>
      </form>
    </div>
  );
}